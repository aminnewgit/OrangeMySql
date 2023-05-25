"""
1、显示方式：
  0（默认）、1（高亮）、22（非粗体）、4（下划线）、24（非下划线）、 5（闪烁）、25（非闪烁）、7（反显）、27（非反显）
2、前景色：
  30（黑色）、31（红色）、32（绿色）、 33（×××）、34（蓝色）、35（洋 红）、36（青色）、37（白色）
3、背景色:
  40（黑色）、41（红色）、42（绿色）、 43（×××）、44（蓝色）、45（洋 红）、46（青色）、47（白色

print("\033[1;2;3m {}\033[0m")
# -*- coding:utf-8 -*-
print("\033[1;30m 字体颜色：白色\033[0m")
print("\033[1;31m 字体颜色：红色\033[0m")
print("\033[1;32m 字体颜色：深黄色\033[0m")
print("\033[1;33m 字体颜色：浅黄色\033[0m")
print("\033[1;34m 字体颜色：蓝色\033[0m")
print("\033[1;35m 字体颜色：淡紫色\033[0m")
print("\033[1;36m 字体颜色：青色\033[0m")
print("\033[1;37m 字体颜色：灰色\033[0m")
print("\033[1;38m 字体颜色：浅灰色\033[0m")

print("背景颜色：白色   \033[1;40m    \033[0m")
print("背景颜色：红色   \033[1;41m    \033[0m")
print("背景颜色：深黄色 \033[1;42m    \033[0m")
print("背景颜色：浅黄色 \033[1;43m    \033[0m")
print("背景颜色：蓝色   \033[1;44m    \033[0m")
print("背景颜色：淡紫色 \033[1;45m    \033[0m")
print("背景颜色：青色   \033[1;46m    \033[0m")
print("背景颜色：灰色   \033[1;47m    \033[0m")
"""

red_template = "\033[1;32m{}\033[0m"
green_template = "\033[1;32m{}\033[0m"

def void_print(*args, **kwargs):
  pass


def debug_out(module_name, msg: str, *args, **kwargs):
  msg = msg.format(*args)
  msg = red_template.format(module_name + ": ") + msg
  print(msg,**kwargs)

def out(*args, **kwargs):
  print(*args, **kwargs)

class DebugLog:

  __slots__ = ("_out", "_debug_out","_module_name")

  def __init__(self, module_name, enable : bool):
    self._module_name = module_name
    if enable is True:
      self._out = print
      self._debug_out = debug_out
    else:
      self._out = void_print
      self._debug_out = void_print


  def __call__(self, msg, *args, **kwargs):
    self._debug_out(self._module_name, msg, *args, **kwargs)

  def list(self,list_data):
    if len(list_data) == 0:
      self._out("[]")
    else:
      for d in list_data:
        self._out(d)

  def dict(self, dict_data: dict):
    for k, v in dict_data.items():
      self._out(k, v)

  def print(self, *args, sep=' ', end='\n'):
    self._out(*args, sep=sep, end=end)

  def print_split(self):
    self._out("==========================================")



class InfoLog:
  def __call__(self, *args, sep=' ', end='\n'):
    # todo 使用包装器在生产环境替换未空函数
    print(*args, sep=sep, end=end)

  @staticmethod
  def list(list_data):
    # todo 使用包装器在生产环境替换未空函数
    if len(list_data) == 0:
      print("[]")
    else:
      for d in list_data:
        print(d)

  @staticmethod
  def split_line():
    print("==========================================")

  @staticmethod
  def dict(dict_data: dict):
    for k, v in dict_data.items():
      print(k, v)

# todo 初始化配置, 关闭所有debug 信息

class OrangeLog:
  def __init__(self,name, enable_debug=False):
    self.debug = DebugLog(name,enable_debug)
    self.info = InfoLog()
    self.error = InfoLog()
    self.name = name

  def enable_debug_log(self):
    self.debug = DebugLog(self.name,True)







