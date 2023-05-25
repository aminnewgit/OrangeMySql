import asyncio

from orange_mysql.init import orange_mysql_init_func_factory, OrangeMySqlConfig
from pool_test.aiomysql import create_pool

db_config = {
  "host": '192.168.0.118',
  "port": 49153,
  "user": "root",
  "password": 'junjun3396',
  "db": 'yyjc_dev',
  "enable_debug_info_show": False,
}

config = OrangeMySqlConfig(db_config)


async def main():
  loop = asyncio.get_running_loop()
  _config = {
    "loop": loop,
    "autocommit": True,
    "minsize": 1,
    "maxsize": 16,
    "echo": False,  # 输出Sql 语句
    "pool_recycle": -1,  # 连接被回收的秒数，有助于处理池中的陈旧连接，默认值为 -1，表示禁用回收逻辑。,
    "host": config.host,
    "port": config.port,
    "user": config.user,
    "password": config.password,
    "db": config.db,
  }
  pool = await create_pool(**_config)
  pool.close()




if __name__ == '__main__':
    asyncio.run(main())