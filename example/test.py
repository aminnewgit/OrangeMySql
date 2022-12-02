import asyncio

from orange_mysql.init import orange_mysql_init_func_factory, OrangeMySqlConfig

db_config = {
  "host": '192.168.0.118',
  "port": 49153,
  "user": "root",
  "password": 'junjun3396',
  "db": 'yyjc_dev',
  "enable_debug_info_show": False,
}

db_config = OrangeMySqlConfig(db_config)


init_func = orange_mysql_init_func_factory(db_config)

async def main():
  close_pool = await init_func()
  close_pool()




if __name__ == '__main__':
    asyncio.run(main())