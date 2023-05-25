from orange_mysql.dbutils.pooled_db import PooledDB


import orange_mysql.pymysql as pymysql


def test():
  try:
    sync_pool = PooledDB(
      creator=pymysql,     # 使用链接数据库的模块
      max_connections=6,    # 连接池允许的最大连接数，0和None表示不限制连接数
      min_cached=2,         # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
      blocking=True,       # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
      ping=0,              # ping MySQL服务端，检查是否服务可用。
                           # 0 = None = never,
                           # 1 = default = whenever it is requested,
                           # 2 = when a cursor is created,
                           # 4 = when a query is executed,
                           # 7 = always
      host='localhost',
      port=3306,
      user='root',
      password='silviscene2023',
      database='yyjc_dev',
      charset='utf8'
    )

    # 去连接池中拿一个连接
    conn = sync_pool.connection()

    cursor = conn.cursor()
    cursor.execute('select * from admin_user')
    result = cursor.fetchall()
    print(result)
    cursor.close()
    conn.close()

  # except pymysql.OperationalError as e:
  #   print('数据库操作错误',e)
  #   print(e.args)
  #   return

  finally:
    pass



test()