"""
简易枚举
2022-7
junjun
"""
import types

enum_dict = {}

class EnumValueInvalid(BaseException):
  def __init__(self,msg):
    self.msg = msg


class _EnumDict(dict):
  __slots__ = ('_enum_raw_item_dict','_value_set','_name_set','_enum_name')
  def __init__(self,enum_name):
    super().__init__()
    self._enum_raw_item_dict = {}
    self.__setitem__('__enum_raw_item_dict__', self._enum_raw_item_dict)
    self._value_set = set()
    self._name_set = set()
    self._enum_name = enum_name

  def __setitem__(self, key, value):



    if isinstance(value, types.FunctionType):
      super(_EnumDict, self).__setitem__(key, value)
    elif key.startswith('_'):
      super(_EnumDict, self).__setitem__(key, value)
    else:

      # print('收集类的定义', key, value)

      if type(value) is not tuple or len(value) < 2 :
        raise ValueError(f"enum: {self._enum_name} name: {key} must be (value,desc) ")
      v = value[0]
      if type(v) is not int: raise ValueError(f"enum: {self._enum_name} value of {key}({value[1]}) must be int ")
      elif key in self._name_set: raise KeyError(f"enum: {self._enum_name} name: {key} repeat")
      elif v in self._value_set: raise ValueError(f"enum: {self._enum_name} value: {value} repeat")

      self._enum_raw_item_dict[key] = value
      self._name_set.add(key)
      self._value_set.add(v)


class EnumMeta(type):

  @classmethod
  def __prepare__(mcs, cls_name, bases, **kwargs):
    if cls_name == 'BaseEnum': return {}
    return _EnumDict(cls_name)


  def __new__(mcs, name, bases, class_dict, **kwargs):
    if name == 'BaseEnum':
      return super().__new__(mcs, name, bases, class_dict, **kwargs)

    _name_dict = {}
    _value_dict = {}
    class_dict['__name_dict__'] = _name_dict
    class_dict['__value_dict__'] = _value_dict
    _enum_class = super().__new__(mcs, name, bases, class_dict, **kwargs)
    for k, v in class_dict['__enum_raw_item_dict__'].items():
      _value = v[0]
      _enum = _enum_class(k, _value, v[1])
      _name_dict[k] = _enum
      _value_dict[_value] = _enum
      setattr(_enum_class, k, _enum)
    enum_dict[class_dict.get('__module__')+"."+name] = _enum_class
    return _enum_class


class BaseEnum(metaclass=EnumMeta):

  __slots__ = ("__enum_name__","__value__","__desc__",'__value_type__')

  def __init__(self, name, value, desc):
    self.__enum_name__ = name
    self.__value__ = value
    self.__desc__ = desc
    self.__value_type__ = type(value)

  @classmethod
  def __get_enum_by_value__(cls, value):
    enum = cls.__value_dict__.get(value)
    if enum is None:
      raise EnumValueInvalid(f'{cls.__name__}没有value为{value}的枚举值')
    return enum

  @classmethod
  def __get_enum_by_name__(cls, name):
    enum = cls.__name_dict__.get(name)
    if enum is None:
      raise EnumValueInvalid(f'{cls.__name__}没有name为{name}的枚举值')
    return enum

  @classmethod
  def get(cls,name_or_value):
    enum = cls.__name_dict__.get(name_or_value)
    if enum is None:
      enum = cls.__value_dict__.get(name_or_value)
      if enum is None:
        raise KeyError(f'{cls.__name__}没有name或value为{name_or_value}的枚举值')
    return enum

  @classmethod
  def __get_define_tuple__(cls):
    return tuple(cls.__enum_raw_item_dict__.items())


  def __repr__(self):
    return str(self.__value__)

  def __str__(self):
    return str(self.__value__)


  # todo 大于小于 判断
  # def __lt__(self, other):
  #
  #
  # def __gt__(self, other):

def get_enum_dict():
  return enum_dict

# class AiTaskEventLogTypeEnum(BaseEnum):
#   add = (0, '新增')  # 新增
#   start = (1, '启动')
#
#
# a = AiTaskEventLogTypeEnum.add
