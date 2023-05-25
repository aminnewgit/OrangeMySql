from orange_kit.model import VoBase, VoField
from orange_kit.json import json_dumps

class VoOne(VoBase):
  kid_name:str = VoField('姓名')
  id:int = VoField('id')


class VoTwo(VoOne):
  age:int = VoField('年龄')
  kid_name: str = VoField('外号')


g = VoTwo({'name': 'jack','age': 10,'id': 11})

print(g)
print(isinstance(g,VoBase))
print(json_dumps(g))
print(VoTwo.get_field_define_list())
