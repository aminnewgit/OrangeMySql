"""PooledDB - pooling for DB-API 2 connections.

Implements a pool of steady, thread-safe cached connections
to a database which are transparently reused,
using an arbitrary DB-API 2 compliant database interface module.

This should result in a speedup for persistent applications such as the
application server of "Webware for Python," without loss of robustness.

Robustness is provided by using "hardened" SteadyDB connections.
Even if the underlying database is restarted and all connections
are lost, they will be automatically and transparently reopened.
However, since you don't want this to happen in the middle of a database
transaction, you must explicitly start transactions with the begin()
method so that SteadyDB knows that the underlying connection shall not
be replaced and errors passed on until the transaction is completed.

Measures are taken to make the pool of connections thread-safe.
If the underlying DB-API module is thread-safe at the connection level,
the requested connections may be shared with other threads by default,
but you can also request dedicated connections in case you need them.

For the Python DB-API 2 specification, see:
    https://www.python.org/dev/peps/pep-0249/
For information on Webware for Python, see:
    https://webwareforpython.github.io/w4py/


Usage:

First you need to set up the database connection pool by creating
an instance of PooledDB, passing the following parameters:

    creator: either an arbitrary function returning new DB-API 2
        connection objects or a DB-API 2 compliant database module
    mincached: the initial number of idle connections in the pool
        (the default of 0 means no connections are made at startup)
    maxcached: the maximum number of idle connections in the pool
        (the default value of 0 or None means unlimited pool size)
    maxshared: maximum number of shared connections allowed
        (the default value of 0 or None means all connections are dedicated)
        When this maximum number is reached, connections are
        shared if they have been requested as shareable.
    maxconnections: maximum number of connections generally allowed
        (the default value of 0 or None means any number of connections)
    blocking: determines behavior when exceeding the maximum
        (if this is set to true, block and wait until the number of
        connections decreases, but by default an error will be reported)
    maxusage: maximum number of reuses of a single connection
        (the default of 0 or None means unlimited reuse)
        When this maximum usage number of the connection is reached,
        the connection is automatically reset (closed and reopened).
    setsession: an optional list of SQL commands that may serve to
        prepare the session, e.g. ["set datestyle to german", ...]
    reset: how connections should be reset when returned to the pool
        (False or None to rollback transcations started with begin(),
        the default value True always issues a rollback for safety's sake)
    failures: an optional exception class or a tuple of exception classes
        for which the connection failover mechanism shall be applied,
        if the default (OperationalError, InterfaceError, InternalError)
        is not adequate for the used database module
    ping: an optional flag controlling when connections are checked
        with the ping() method if such a method is available
        (0 = None = never, 1 = default = whenever fetched from the pool,
        2 = when a cursor is created, 4 = when a query is executed,
        7 = always, and all other bit combinations of these values)

    The creator function or the connect function of the DB-API 2 compliant
    database module specified as the creator will receive any additional
    parameters such as the host, database, user, password etc.  You may
    choose some or all of these parameters in your own creator function,
    allowing for sophisticated failover and load-balancing mechanisms.

For instance, if you are using pgdb as your DB-API 2 database module and
want a pool of at least five connections to your local database 'mydb':

    import pgdb  # import used DB-API 2 module
    from dbutils.pooled_db import PooledDB
    pool = PooledDB(pgdb, 5, database='mydb')

Once you have set up the connection pool you can request
database connections from that pool:

    db = pool.connection()

You can use these connections just as if they were ordinary
DB-API 2 connections.  Actually what you get is the hardened
SteadyDB version of the underlying DB-API 2 connection.

Please note that the connection may be shared with other threads
by default if you set a non-zero maxshared parameter and the DB-API 2
module allows this.  If you want to have a dedicated connection, use:

    db = pool.connection(shareable=False)

You can also use this to get a dedicated connection:

    db = pool.dedicated_connection()

If you don't need it any more, you should immediately return it to the
pool with db.close().  You can get another connection in the same way.

Warning: In a threaded environment, never do the following:

    pool.connection().cursor().execute(...)

This would release the connection too early for reuse which may be
fatal if the connections are not thread-safe.  Make sure that the
connection object stays alive as long as you are using it, like that:

    db = pool.connection()
    cur = db.cursor()
    cur.execute(...)
    res = cur.fetchone()
    cur.close()  # or del cur
    db.close()  # or del db

You can also use context managers for simpler code:

    with pool.connection() as db:
        with db.cursor as cur:
            cur.execute(...)
            res = cur.fetchone()

Note that you need to explicitly start transactions by calling the
begin() method.  This ensures that the connection will not be shared
with other threads, that the transparent reopening will be suspended
until the end of the transaction, and that the connection will be rolled
back before being given back to the connection pool.


Ideas for improvement:

* Add a thread for monitoring, restarting (or closing) bad or expired
  connections (similar to DBConnectionPool/ResourcePool by Warren Smith).
* Optionally log usage, bad connections and exceeding of limits.


Copyright, credits and license:

* Contributed as supplement for Webware for Python and PyGreSQL
  by Christoph Zwerschke in September 2005
* Based on the code of DBPool, contributed to Webware for Python
  by Dan Green in December 2000

Licensed under the MIT license.
"""

from threading import Condition

from . import __version__
from .steady_db import connect


class PooledDBError(Exception):
    """General PooledDB error."""


class InvalidConnection(PooledDBError):
    """Database connection is invalid."""


class NotSupportedError(PooledDBError):
    """DB-API module not supported by PooledDB."""


class TooManyConnections(PooledDBError):
    """Too many database connections were opened."""


class PooledDB:
    """Pool for DB-API 2 connections.

    After you have created the connection pool, you can use
    connection() to get pooled, steady(稳定的) DB-API 2 connections.
    """

    version = __version__

    def __init__(
            self, creator, min_cached=0, max_cached=0,
            max_shared=0, max_connections=0, blocking=False,
            max_usage=None, set_session=None, reset=True,
            failures=None, ping=1,
            *args, **kwargs):
        """Set up the DB-API 2 connection pool.

        creator: either an arbitrary function returning new DB-API 2
            connection objects or a DB-API 2 compliant database module
            链接创建者-返回新DB-API 2连接对象的任意函数或符合DB-API的数据库模块
        min_cached: initial number of idle connections in the pool
            (0 means no connections are made at startup)
            最小缓存-池中空闲连接的初始数量(0意味着开始时没有连接)
        max_cached: maximum number of idle connections in the pool
            (0 or None means unlimited pool size)
            池中空闲连接的最大数量(0或None表示池大小不受限制)
        max_shared: maximum number of shared connections
            (0 or None means all connections are dedicated)
            最大共享连接数(0或None表示所有连接都是专用的)
            When this maximum number is reached, connections are
            shared if they have been requested as shareable.
            当达到这个最大数量时，如果连接已被请求为可共享，则连接将被共享。
        max_connections: maximum number of connections generally allowed
            (0 or None means an arbitrary number of connections)
            通常允许的最大连接数(0或None表示任意数量的连接)
        blocking: determines behavior when exceeding the maximum
            (if this is set to true, block and wait until the number of
            connections decreases, otherwise an error will be reported)
            确定超过最大值时的行为（如果设置为true，则阻止并等待，直到连接数量减少，否则将报告错误）
        max_usage: maximum number of reuses of a single connection
            (0 or None means unlimited reuse)
            When this maximum usage number of the connection is reached,
            the connection is automatically reset (closed and reopened).
            单个连接的最大重用次数（0或None表示无限制重用）
            当达到连接的最大使用次数时，连接将自动重置（关闭并重新打开）。
        set_session: optional list of SQL commands that may serve to prepare
            the session, e.g. ["set datestyle to ...", "set time zone ..."]
            可用于准备会话的SQL命令的可选列表
        reset: how connections should be reset when returned to the pool
            (False or None to rollback transcations started with begin(),
            True to always issue a rollback for safety's sake)
            返回到池时应如何重置连接 并不是很理解
        failures: an optional exception class or a tuple of exception classes
            for which the connection failover mechanism shall be applied,
            if the default (OperationalError, InterfaceError, InternalError)
            is not adequate for the used database module
            如果默认值（OperationalError、InterfaceError、InternalError）
            不适用于所使用的数据库模块，则应为其应用连接故障转移机制的可选异常类或异常类元组
        ping: determines when the connection should be checked with ping()
            确定何时应使用ping（）检查连接
            (0 = None = never,
            1 = default = whenever fetched from the pool,
            2 = when a cursor is created,
            4 = when a query is executed,
            7 = always, and all other bit combinations of these values)
        args, kwargs: the parameters that shall be passed to the creator
            function or the connection constructor of the DB-API 2 module
            应传递给DB-API 2模块的创建者函数或连接构造函数的参数
        """
        try:
            threadsafety = creator.threadsafety
        except AttributeError:
            try:
                if not callable(creator.connect):
                    raise AttributeError
            except AttributeError:
                threadsafety = 2
            else:
                threadsafety = 0
        if not threadsafety:
            raise NotSupportedError("Database module is not thread-safe.")
        self._creator = creator
        self._args, self._kwargs = args, kwargs
        self._blocking = blocking
        self._max_usage = max_usage
        self._set_session = set_session
        self._reset = reset
        self._failures = failures
        self._ping = ping

        # ===初始化参数
        if min_cached is None:
            min_cached = 0
        if max_cached is None:
            max_cached = 0
        if max_connections is None:
            max_connections = 0
        if max_cached:
            if max_cached < min_cached:
                max_cached = min_cached
            self._max_cached = max_cached
        else:
            self._max_cached = 0
        if threadsafety > 1 and max_shared:
            self._max_shared = max_shared
            self._shared_cache = []  # the cache for shared connections
        else:
            self._max_shared = 0
        if max_connections:
            if max_connections < max_cached:
                max_connections = max_cached
            if max_connections < max_shared:
                max_connections = max_shared
            self._max_connections = max_connections
        else:
            self._max_connections = 0
        self._idle_cache = []
        # the actual pool of idle connections
        self._lock = Condition()
        self._connections = 0

    def init(self):

        # Establish an initial number of idle database connections:
        # 建立空闲数据库连接的初始数量
        idle = [self.dedicated_connection() for i in range(min_cached)]

        while idle:
            idle.pop().close()

    def steady_connection(self):
        """
        获取一个稳定的没有在池中的链接
        Get a steady, unpooled DB-API 2 connection.
        """
        return connect(
            self._creator, self._max_usage, self._set_session,
            self._failures, self._ping, True, *self._args, **self._kwargs)

    def connection(self, shareable=True):
        """Get a steady, cached DB-API 2 connection from the pool.

        If shareable is set and the underlying DB-API 2 allows it,
        then the connection may be shared with other threads.
        如果设置了可共享，并且底层DB-API 2允许，那么该连接可以与其他线程共享。
        """
        if shareable and self._max_shared:
            with self._lock:
                while (not self._shared_cache and self._max_connections
                        and self._connections >= self._max_connections):
                    self._wait_lock()
                if len(self._shared_cache) < self._max_shared:
                    # shared cache is not full, get a dedicated connection
                    try:  # first try to get it from the idle cache
                        con = self._idle_cache.pop(0)
                    except IndexError:  # else get a fresh connection
                        con = self.steady_connection()
                    else:
                        con._ping_check()  # check this connection
                    con = SharedDBConnection(con)
                    self._connections += 1
                else:  # shared cache full or no more connections allowed
                    self._shared_cache.sort()  # least shared connection first
                    con = self._shared_cache.pop(0)  # get it
                    while con.con._transaction:
                        # do not share connections which are in a transaction
                        self._shared_cache.insert(0, con)
                        self._wait_lock()
                        self._shared_cache.sort()
                        con = self._shared_cache.pop(0)
                    con.con._ping_check()  # check the underlying connection
                    con.share()  # increase share of this connection
                # put the connection (back) into the shared cache
                self._shared_cache.append(con)
                self._lock.notify()
            con = PooledSharedDBConnection(self, con)
        else:  # try to get a dedicated connection
            with self._lock:
                while (self._max_connections
                        and self._connections >= self._max_connections):
                    self._wait_lock()
                # connection limit not reached, get a dedicated connection
                try:  # first try to get it from the idle cache
                    con = self._idle_cache.pop(0)
                except IndexError:  # else get a fresh connection
                    con = self.steady_connection()
                else:
                    con._ping_check()  # check connection
                # 池专用DB连接
                con = PooledDedicatedDBConnection(self, con)
                self._connections += 1
        return con

    def dedicated_connection(self):
        """
        专用连接
        Alias for connection(shareable=False).
        """
        return self.connection(False)

    def unshare(self, con):
        """Decrease the share of a connection in the shared cache."""
        with self._lock:
            con.unshare()
            shared = con.shared
            if not shared:  # connection is idle,
                try:  # so try to remove it
                    self._shared_cache.remove(con)  # from shared cache
                except ValueError:
                    pass  # pool has already been closed
        if not shared:  # connection has become idle,
            self.cache(con.con)  # so add it to the idle cache

    def cache(self, con):
        """Put a dedicated connection back into the idle cache."""
        with self._lock:
            if not self._max_cached or len(self._idle_cache) < self._max_cached:
                con._reset(force=self._reset)  # rollback possible transaction
                # the idle cache is not full, so put it there
                self._idle_cache.append(con)  # append it to the idle cache
            else:  # if the idle cache is already full,
                con.close()  # then close the connection
            self._connections -= 1
            self._lock.notify()

    def close(self):
        """Close all connections in the pool."""
        with self._lock:
            while self._idle_cache:  # close all idle connections
                con = self._idle_cache.pop(0)
                try:
                    con.close()
                except Exception:
                    pass
            if self._max_shared:  # close all shared connections
                while self._shared_cache:
                    con = self._shared_cache.pop(0).con
                    try:
                        con.close()
                    except Exception:
                        pass
                    self._connections -= 1
            self._lock.notify_all()

    def __del__(self):
        """Delete the pool."""
        try:
            self.close()
        except:  # builtin Exceptions might not exist any more
            pass

    def _wait_lock(self):
        """Wait until notified or report an error."""
        if not self._blocking:
            raise TooManyConnections
        self._lock.wait()


# Auxiliary classes for pooled connections

class PooledDedicatedDBConnection:
    """Auxiliary proxy class for pooled dedicated connections."""

    def __init__(self, pool, con):
        """Create a pooled dedicated connection.

        pool: the corresponding PooledDB instance
        con: the underlying SteadyDB connection
        """
        # basic initialization to make finalizer work
        self._con = None
        # proper initialization of the connection
        if not con.threadsafety():
            raise NotSupportedError("Database module is not thread-safe.")
        self._pool = pool
        self._con = con

    def close(self):
        """Close the pooled dedicated connection."""
        # Instead of actually closing the connection,
        # return it to the pool for future reuse.
        if self._con:
            self._pool.cache(self._con)
            self._con = None

    def __getattr__(self, name):
        """Proxy all members of the class."""
        if self._con:
            return getattr(self._con, name)
        raise InvalidConnection

    def __del__(self):
        """Delete the pooled connection."""
        try:
            self.close()
        except:  # builtin Exceptions might not exist any more
            pass

    def __enter__(self):
        """Enter a runtime context for the connection."""
        return self

    def __exit__(self, *exc):
        """Exit a runtime context for the connection."""
        self.close()


class SharedDBConnection:
    """Auxiliary class for shared connections."""

    def __init__(self, con):
        """Create a shared connection.

        con: the underlying SteadyDB connection
        """
        self.con = con
        self.shared = 1

    def __lt__(self, other):
        if self.con._transaction == other.con._transaction:
            return self.shared < other.shared
        return not self.con._transaction

    def __le__(self, other):
        if self.con._transaction == other.con._transaction:
            return self.shared <= other.shared
        return not self.con._transaction

    def __eq__(self, other):
        return (self.con._transaction == other.con._transaction
                and self.shared == other.shared)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return other.__lt__(self)

    def __ge__(self, other):
        return other.__le__(self)

    def share(self):
        """Increase the share of this connection."""
        self.shared += 1

    def unshare(self):
        """Decrease the share of this connection."""
        self.shared -= 1


class PooledSharedDBConnection:
    """Auxiliary proxy class for pooled shared connections."""

    def __init__(self, pool, shared_con):
        """Create a pooled shared connection.

        pool: the corresponding PooledDB instance
        con: the underlying SharedDBConnection
        """
        # basic initialization to make finalizer work
        self._con = None
        # proper initialization of the connection
        con = shared_con.con
        if not con.threadsafety() > 1:
            raise NotSupportedError("Database connection is not thread-safe.")
        self._pool = pool
        self._shared_con = shared_con
        self._con = con

    def close(self):
        """Close the pooled shared connection."""
        # Instead of actually closing the connection,
        # unshare it and/or return it to the pool.
        if self._con:
            self._pool.unshare(self._shared_con)
            self._shared_con = self._con = None

    def __getattr__(self, name):
        """Proxy all members of the class."""
        if self._con:
            return getattr(self._con, name)
        raise InvalidConnection

    def __del__(self):
        """Delete the pooled connection."""
        try:
            self.close()
        except:  # builtin Exceptions might not exist any more
            pass

    def __enter__(self):
        """Enter a runtime context for the connection."""
        return self

    def __exit__(self, *exc):
        """Exit a runtime context for the connection."""
        self.close()
