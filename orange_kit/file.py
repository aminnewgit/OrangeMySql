import os.path


def ensure_dir_exist(path:str):
  path = path.strip()
  if path != '' and  os.path.exists(path) is False:
    os.makedirs(path)
  return path

# todo 规范路径函数
