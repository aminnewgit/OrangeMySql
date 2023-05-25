class MateSingleton(type):
  __instance_dict = {}
  def __call__(cls, *args, **kwargs):
    instance = cls.__instance_dict.get(cls)
    if instance is None:
      instance = super(MateSingleton, cls).__call__(*args, **kwargs)
      cls.__instance_dict[cls] = instance
    return instance


class SingletonCom(metaclass=MateSingleton):
  pass