from typing import TypeVar, Generic


# todo 定义一种封装类型, 用于定义api 函数的返回值, 一种泛型支持, 看看怎么融入的VoBase里面

T = TypeVar('T')
class RespWrapClass(Generic[T]):
  pass

# todo 重点在 vo 继承泛型

# 快速实现 做个单独的封装类, 指定好信息

#
#
# T = TypeVar('T')
#
# class T1(Generic[T]):
#   pass
#
#
# def get_value() -> T1[int]:
#   r = T1()
#   r.one = 123
#   return r
#
# sig = signature(get_value)
# return_type = sig.return_annotation
#
# print(dir(return_type))
# print(return_type.__args__)  # 这里存储泛型 元组
# print(return_type.__name__)
#
# print(sig)
