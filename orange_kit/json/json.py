import datetime
import json

from orange_kit.model import VoBase, BaseEnum

class __JsonEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, datetime.datetime):
      return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, datetime.date):
      return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, VoBase):
      return obj.get_camel_case_dict()
    elif isinstance(obj, BaseEnum):
      return obj.__enum_name__
    else:
      return json.JSONEncoder.default(self, obj)

def json_dumps(data):
  return json.dumps(
    data,
    cls=__JsonEncoder,
    ensure_ascii=False,
    separators=(',', ':')
    # indent=2 # 缩进
  )

def json_loads(string):
  return json.loads(string)