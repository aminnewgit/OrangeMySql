from orange_kit.log import OrangeLog


def escape_arg(arg):
  arg = arg.replace("'", "''")
  return f"'{arg}'"


def get_values_placeholder(length):
  p_list = []
  for i in range(length):
    p_list.append("%s")
  return ','.join(p_list)




log = OrangeLog()