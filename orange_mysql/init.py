import asyncio

from orange_kit.model import VoBase, VoField

from .aiomysql import create_pool
from .aiomysql.pool import Pool
from .utils import orange_sql_log, config_debug_log


# todo 可以初始化多个数据, 多数据可进行命名, 在定义rope的时候可以根据名字选择数据库
# todo 做一个脱离api 可执行的方式
# todo api 里面统一配置
# todo 像 spring boot 一样yml 自动配置, 生成yml schema



class OrangeMySqlConfig(VoBase):
  """
  mysql 配置
  -----
  Parameters

  """
  host:str       = VoField("host地址 例如 192.168.1.50",)
  port:int       = VoField("端口", default=3306)
  user:str       = VoField("用户名")
  password:str   = VoField("密码")
  db:str         = VoField("数据库")

  enable_debug_info_show: bool = VoField("输出开发信息",default=False)


  def get_conn_str(self):
    return f"mysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}?charset=uft8"


sql_pool = None

def orange_mysql_init(config: OrangeMySqlConfig):

  config_debug_log(config.enable_debug_info_show)

  async def init_func():
    global sql_pool
    loop = asyncio.get_running_loop()
    _config = {
      "loop": loop,
      "autocommit": True,
      "minsize": 1,
      "maxsize": 16,
      "echo": False,       # 输出Sql 语句
      "pool_recycle": -1,  # 连接被回收的秒数，有助于处理池中的陈旧连接，默认值为 -1，表示禁用回收逻辑。,
      "host": config.host,
      "port": config.port,
      "user": config.user,
      "password": config.password,
      "db": config.db,
    }
    orange_sql_log.debug(f"orange mysql connect to {config.host}:{config.port}", end=" ")

    pool = await create_pool(**_config)
    orange_sql_log.debug("ok")
    sql_pool = pool

    def close_pool():
      pool.close()
    return close_pool

  return init_func

def get_sql_pool()->Pool:
  return sql_pool


