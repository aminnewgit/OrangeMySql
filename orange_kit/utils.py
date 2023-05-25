import datetime
import os
import time


def line_to_hump(string):
  upper = False
  new_str = ''
  for char in string:
    if upper is True:
      new_str += char.upper()
      upper = False
    elif char == '_':
      upper = True
    else:
      new_str += char
  return new_str

def get_now():
  return datetime.datetime.now()

def get_now_timestamp():
  """秒为单位的浮点数-的时间戳"""
  return time.time()

def get_date_str():
  """返回字符格式日期20220919 """
  now = datetime.datetime.now()
  return str(now.date()).replace('-', '')

def get_date_str_with_underline():
  """返回字符格式日期20220919 """
  now = datetime.datetime.now()
  return str(now.date())

def write_json_file(path, data):
  from .json import json_dumps
  data = json_dumps(data).encode('utf-8')
  with open(path, 'wb') as f:
    f.write(data)


def read_json_file(path):
 from .json import json_loads
 if os.path.exists(path) is False:
    return None
 with open(path, 'r', encoding='utf-8') as f:
   data = f.read()
 return json_loads(data)

