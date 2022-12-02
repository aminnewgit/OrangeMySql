from orange_kit.log import OrangeLog


def escape_arg(arg):
  arg = arg.replace("'", "''")
  return f"'{arg}'"


def get_values_placeholder(length):
  p_list = []
  for i in range(length):
    p_list.append("%s")
  return ','.join(p_list)


orange_sql_log = OrangeLog("orange_mysql")

def config_debug_log(show_dev_info: bool):
  if show_dev_info is True:
    orange_sql_log.enable_debug_log()

class SqlError(Exception):
  def __init__(self,msg):
    self.msg = msg

