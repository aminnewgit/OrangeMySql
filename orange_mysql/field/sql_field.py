# 数据库字段
from orange_kit.model import VoField


class SqlField(VoField):

  __slots__ = ('map_json','not_null')

  def __init__(self, desc, default=None, not_null=False, map_json=False):
    super().__init__(desc, default)
    self.map_json = map_json
    self.not_null: bool = not_null