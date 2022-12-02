from typing import TypeVar

from orange_kit.model.exception import FieldValidationError
from orange_kit.model.type_converter import get_type_converter
from orange_kit.utils import line_to_hump

# todo 把名字形式转换器后期单独抽象到一个类, 或者 反倒反序列化时做, 可以配置的 用alias(别名) 作为描述

def get_generic_type(typ):
  generic = {}
  for index, t_n in enumerate(typ.__origin__.__parameters__):
    generic[t_n.__name__] = get_type_define(typ.__args__[index])
  return generic

def get_type_define(typ):
  from orange_kit.model import VoBase
  from orange_kit.model import BaseEnum

  # todo 联合类型出错
  try:
    if typ.__class__.__name__ == "_GenericAlias":
      generic = get_generic_type(typ)
      typ = {'name': f"{typ.__module__}.{typ.__name__}", "generic": generic}
    elif isinstance(typ, TypeVar):
      typ = typ.__name__
    elif isinstance(typ, type):
      if hasattr(typ, "__args__"):
        generic = [get_type_define(t) for t in typ.__args__]
        typ = {'name': typ.__name__, "generic": generic}
      elif issubclass(typ, (VoBase, BaseEnum)) is True:
        typ = f"{typ.__module__}.{typ.__name__}"
      else:
       typ = typ.__name__
    elif issubclass(typ, (VoBase, BaseEnum)) is True:
      typ = f"{typ.__module__}.{typ.__name__}"
    else:
      typ = typ.__name__
    return typ
  except TypeError:
    return typ.__repr__()



class VoField:
  """
  基础值类型
  """
  __slots__ = ('class_name', 'desc', "name",
               'index', 'camel_case', 'type',
               'default', 'type_converter',
               'get_value_from_dict_func')

  def __init__(self,desc,default=None):
    self.class_name = None
    self.desc = desc
    self.name = None
    self.index = None
    self.camel_case = None
    self.type = None
    self.default = default

    self.type_converter = None
    self.get_value_from_dict_func = None

  def init(self):
    self.camel_case = line_to_hump(self.name)  # 转驼峰
    self.set_type_converter()
    self.set_get_value_from_dict_func()

  def get_value(self, val):
    return self.type_converter(val,self)

  def get_value_from_dict(self, input_dict):
    val = self.get_value_from_dict_func(input_dict)
    if val is None: return val
    return self.type_converter(val)

  # 获取类型转换器
  def set_type_converter(self):
    self.type_converter = get_type_converter(self)

  # 从字典获取值
  def set_get_value_from_dict_func(self):
    if self.camel_case == self.name:
      self.get_value_from_dict_func = self.__get_value_from_dict_direct__
    else:
      self.get_value_from_dict_func = self.__get_value_from_dict_with_camel_case__
  def __get_value_from_dict_with_camel_case__(self,input_dict):
    val = input_dict.get(self.camel_case)
    if val is None:
      val = input_dict.get(self.name, self.default)
    return val
  def __get_value_from_dict_direct__(self,input_dict):
    return input_dict.get(self.name, self.default)


  # 获取字段定义, 用于文档一类
  def get_field_define_dict(self):
    typ = get_type_define(self.type)
    return {
      "name" : self.name,
      "camel_case" : self.camel_case,
      "type" : typ,
      "desc": self.desc,
      "default" : self.default,
    }

  def __repr__(self):
    return f"VoField {self.name}"




# valid Validation
# todo 其他验证通关dto的验证list 来实现,  require 只是不能为None 不能为空用 not_empty
# todo dto 有两各处理list 一个value_pipe 值管道,用于处理值,  另外一个是验证列表 valid_list, 当然在管道中也可以做验证

# todo require 分为两部分 not_none 和 not_empty
# 基础类型需要做not_empty 验证的有,  这个也要放到数据库 where_if 也需要,

# 传输对象字段
class DtoField(VoField):
  __slots__ = ("require",)
  def __init__(self, desc, default=None, require=False):
    super().__init__(desc,default=default)
    self.require = require

  def get_value_from_dict(self, input_dict):
    val = self.get_value_from_dict_func(input_dict)
    if val is None:
      if self.require is True:
        raise FieldValidationError(f'{self.name}是必填字段')
    else:
      val = self.type_converter(val)
      val = self.verify_value(val)
    return val

  def verify_value(self, val):
    # todo 获取类型验证函数 比如 str require 就是不能为空, 字段可以加入规则list, 不支持async
    # todo 初始化字段的时候自动选择验证器
    if self.type is str:
      val = val.strip()
      if self.require is True and val == "":
        raise FieldValidationError(f'{self.name}是必填字段并且不为空')
    return val

  def get_field_define_dict(self):
    define_dict = super().get_field_define_dict()
    define_dict['require'] = self.require
    return define_dict

# 用于带有泛型的包装类定义, 只能做类型指示不做实例化使用,一般用于返回值
class WrapField(VoField):
  __slots__ = ("alias",)
  def __init__(self, desc, default=None,alias=None):
    super().__init__(desc,default=default)
    self.alias = alias

  def init(self):
    self.camel_case = line_to_hump(self.name)  # 转驼峰

  def get_field_define_dict(self):
    define_dict = super().get_field_define_dict()
    if self.alias is not None:
      define_dict['name'] = self.alias
    return define_dict




