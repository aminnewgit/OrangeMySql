
# ==============类型转换======================


from types import GenericAlias

from .base_enum import BaseEnum
from .exception import FieldValidationError

# 未作转换定义的类型, 不做转换
def void_converter(val):
  return val

def void_converter_factory(field, ex_msg):
  return void_converter


# 基础类型 str, int, float, bool, None, dict, list
# 包装类型 list[int], dict[str,int], 这个隶属types. GenericAlias
# 封装类型 enum, VoBase 要个要用子类判断


# require 分为两部分 not_none 和 not_empty
# 不同类型的not empty 是不同范畴 有些地方只需要转换,不需要验证,所以分开,之类就不做empty的验证了


# ==基础类型==
def str_converter_factory(field, ex_msg):
  return str

def int_converter_factory(field, ex_msg):
  def converter(val):
    try:
      return int(val)
    except ValueError:
      msg = f'字段{field.name}的{ex_msg}必须是int类型'
      raise FieldValidationError(msg)
  return converter

def float_converter_factory(field, ex_msg):
  def converter(val):
    try:
      return float(val)
    except ValueError:
      msg = f'字段{field.name}的{ex_msg}必须是float类型'
      raise FieldValidationError(msg)
  return converter

def bool_converter_factory(field, ex_msg):
  return bool

def list_converter_factor(field, ex_msg, sub_type_tuple=None):

  if sub_type_tuple is None:
    def converter(val):
      if type(val) != list:
        raise FieldValidationError(f'字段{field.name}的{ex_msg}必须是list(array)类型')
      return val
    return converter

  item_type = sub_type_tuple[0]
  item_converter = get_type_converter(item_type,"元素")

  def converter(val):
    if type(val) != list:
      raise FieldValidationError(f'字段{field.name}的{ex_msg}必须是list(array)类型')
    res = []
    for element_val in val:
      res.append(item_converter(element_val))
    return res

  return converter

def dict_converter_factor(field, ex_msg, sub_type_tuple=None):

  if sub_type_tuple is None:
    def converter(val):
      if type(val) != dict:
        raise FieldValidationError(f'字段{field.name}的{ex_msg}必须是dict(object)类型')
      return val
    return converter

  key_type = sub_type_tuple[0]
  key_converter = get_type_converter(key_type,'key')

  value_type = sub_type_tuple[1]
  value_converter = get_type_converter(value_type,'value')

  def converter(val):
    if type(val) != dict:
      raise FieldValidationError(f'字段{field.name}的{ex_msg}必须是dict(object)类型')
    res = {}
    for k,v in val.items():
      k = key_converter(k)
      v = value_converter(v)
      res[k] = v
    return res

  return converter

# ==包装类型==
def generic_alias_converter_factory(field, ex_msg):
  typ = field.type
  wrap_class = typ.__origin__
  sub_type_tuple = typ.__args__
  cf = converter_factory_dict.get(wrap_class)
  if cf is None:
    return void_converter
  else:
    return cf(field,ex_msg,sub_type_tuple)

# ==封装类型== 转换器
def enum_converter_factory(field, ex_msg='值'):
  typ = field.type
  name = field.name
  def converter(val):
    if isinstance(val, typ): return val
    try:
      return typ.get(val)
    except KeyError:
      msg = f'字段{name}的{ex_msg}没有在枚举范围内'
      raise FieldValidationError(msg)
  return converter

def vo_converter_factory(field, ex_msg='值'):
  from orange_kit.model import VoBase
  def converter(val):
    typ = field.type
    if isinstance(val,typ): return val
    elif isinstance(val,VoBase): return typ(val.__dict__)
    elif isinstance(val,dict): return typ(val)
    else:
      raise FieldValidationError(f'字段{field.name}的{ex_msg}类型错误')
  return converter

# 类型直查
converter_factory_dict = {
  str: str_converter_factory,
  int: int_converter_factory,
  float: float_converter_factory,
  bool: bool_converter_factory,
  list: list_converter_factor,
  dict: dict_converter_factor,
  # tuple: void_converter_factory,
  any: void_converter_factory,
  GenericAlias: generic_alias_converter_factory,
}


# ==递归获取转换器==
# 需要额外扩展的类型转换器, 自定义一个类型转换器工厂函数
def get_type_converter(field,ex_converter_factory=None):
  from orange_kit.model import VoBase
  typ = field.type
  ex_msg = '值'
  converter_factory = converter_factory_dict.get(typ)
  try:
    if converter_factory is not None:
      return converter_factory(field,ex_msg)
    elif issubclass(typ, BaseEnum):
      return enum_converter_factory(field,ex_msg)
    elif issubclass(typ, VoBase):
      return vo_converter_factory(field,ex_msg)
    elif ex_converter_factory is not None:
      converter = ex_converter_factory(field,ex_msg)
      if converter is None:
        return void_converter
    else:
      return void_converter
  except TypeError:
    return void_converter



