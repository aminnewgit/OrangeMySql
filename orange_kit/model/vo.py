from abc import ABCMeta
from typing import Generic

from .field import VoField
from .exception import VoBaseClassInheritError, FieldDefineError

vo_dict = {}

def create_field(class_name,namespace,field_name,field_type,index):
  # 处理字段定义
  field = namespace.get(field_name)

  if field is None:
    raise FieldDefineError(f'类:{class_name}的字段:{field_name} 的字段定义没有设置')
  elif isinstance(field,VoField) is False:
    raise FieldDefineError(f'类:{class_name}的字段:{field_name} 的字段定义 不是VoField或他的子类')

  field.class_name = class_name
  field.name = field_name
  field.type = field_type
  field.index = index
  field.init()
  return field

def init_value_object(class_name,namespace):
  field_list = []
  field_dict = {}
  field_name_list = []
  # field_camel_case_dict = {} # 用于后期json序列化适配 alias(别名)

  an_dict = namespace.get("__annotations__")
  if an_dict is not None:
    for index, (field_name, field_type) in enumerate(an_dict.items()):
      # 处理字段定义
      field = create_field(class_name,namespace,field_name,field_type,index)
      # 字段索引
      field_list.append(field)
      field_dict[field_name] = field
      field_name_list.append(field_name)
      # 给类 属性复制 属性名 方便快速引用
      namespace[field_name] = field_name

  namespace["__field_name_list__"] = tuple(field_name_list)
  namespace["__field_list__"] = tuple(field_list)
  namespace["__field_dict__"] = field_dict

def inherit_value_object(class_name,parent_class,namespace):
  field_name_list = list(parent_class.__field_name_list__)
  field_list = list(parent_class.__field_list__)
  field_dict = {}
  field_dict.update(parent_class.__field_dict__)
  field_index_base = len(field_list) - 1

  an_dict:dict[str:any] = namespace.get("__annotations__")
  if an_dict is not None:
    for index, (field_name, field_type) in enumerate(an_dict.items()):
      # 处理字段定义
      # 处理字段定义
      field = create_field(class_name,namespace, field_name, field_type, index)
      # 处理重写
      parent_field = field_dict.get(field_name)
      if parent_field is None:
        # 字段索引
        field.index += field_index_base
        field_list.append(field)
        field_name_list.append(field_name)
      else:
        index = parent_field.index
        field.index = index
        field_list[index] = field

      field_dict[field_name] = field
      # 给类 属性复制 属性名 方便快速引用
      namespace[field_name] = field_name

  namespace["__field_name_list__"] = tuple(field_name_list)
  namespace["__field_list__"] = tuple(field_list)
  namespace["__field_dict__"] = field_dict

def create_vo_class(name, bases, namespace):
  # 用不同field来处理不同的业务,所以 VoBase 不会继承出新的基础类型
  parent_class = bases[0]
  if parent_class is VoBase:
    init_value_object(name, namespace)
  elif issubclass(parent_class, VoBase):
    inherit_value_object(name, parent_class, namespace)
  else:
    raise VoBaseClassInheritError(f'类:{name}不能继承非VoBase子类的类:{parent_class.__name__}')

def create_generic_vo_warp_class(name, bases, namespace):
  # 处理带有泛型的封装类, 只用作类型指示
  parent_class = bases[0]
  parent2_is_generic_alias = bases[1] is Generic
  if parent_class is VoBase and parent2_is_generic_alias:
    init_value_object(name, namespace)
  elif issubclass(parent_class, VoBase) and parent2_is_generic_alias:
    inherit_value_object(name, parent_class, namespace)
  else:
    raise VoBaseClassInheritError(f'类:{name}不能继承非VoBase子类的类:{parent_class.__name__}')


class __VoMetaclass(ABCMeta):
  def __new__(mcs, name, bases, namespace, **kwargs):
    if name == "VoBase":
      return super().__new__(mcs, name, bases, namespace, **kwargs)

    if len(bases) == 1:
      create_vo_class(name, bases, namespace)
    elif len(bases) == 2:
      create_generic_vo_warp_class(name, bases, namespace)
    else:
      raise VoBaseClassInheritError("VoBase 类只支持单继承")

    # else: 没有继承的情况只有 VoBase 初始化的时候才有所以什么都不用做
    vo_class = super().__new__(mcs, name, bases, namespace, **kwargs)
    vo_dict[namespace.get('__module__') + "." + name] = vo_class
    return vo_class


class VoBase(metaclass=__VoMetaclass):
  __field_name_list__: tuple
  __field_list__: tuple
  __field_dict__: dict

  def get_camel_case_dict(self):
    data = self.__dict__
    out_dict = {}
    for field in self.__class__.__field_list__:
      out_dict[field.camel_case] = data.get(field.name)
    return out_dict

  @classmethod
  def get_field_define_list(cls):
    return [field.get_field_define_dict() for field in cls.__field_list__]


  def __repr__(self):
    return f"{self.__class__.__name__} {self.__dict__.__repr__()}"

  def __init__(self,data_dict=None):
    field_list = self.__class__.__field_list__

    if data_dict is None :
      for field in field_list:
        self.__setattr__(field.name, field.default)
    elif type(data_dict) is dict:
      for field in field_list:
        val = field.get_value_from_dict(data_dict)
        self.__setattr__(field.name,val)
    else:
      raise ValueError(f'类: {self.__class__.__name__} 初始化参数必须是None或dict')


def get_vo_base_dict():
  return vo_dict