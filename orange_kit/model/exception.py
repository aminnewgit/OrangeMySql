

class FieldValidationError(BaseException):
  """
  字段验证异常
  """
  def __init__(self,msg):
    self.msg = msg


class FieldDefineError(BaseException):
  """
  字段定义错误
  """
  def __init__(self,msg):
    self.msg = msg


class VoBaseClassInheritError(BaseException):
  """
  类继承错误
  """
  def __init__(self,msg):
    self.msg = msg