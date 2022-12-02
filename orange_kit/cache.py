"""
简易缓存, 不方便使redis时使用, 不适合数据量比较大的场景
jun
2022-8-3
"""
import asyncio
import os.path

from .file import ensure_dir_exist
from .model import VoBase, DtoField
from .utils import write_json_file, read_json_file




class CacheKeyItem:

  __slots__ = ("data","ttl")

  def __init__(self,data,expire:int):
    self.data = data
    self.ttl = expire # 到期时间剩余
    # self.expire = int(time.time() + expire)

  def to_dict(self):
    return {
      "v": self.data,
      "ex": self.ttl,
    }


class Cache:

  __slots__ = ("key_dict", "polling_time", "task",
               "run", "save_file_name")

  def __init__(self,save_file_path=''):
    self.key_dict:dict[str, CacheKeyItem] = {}
    self.polling_time = 2 # 轮询时间单位秒
    self.task = None
    self.run = False
    save_file_path = ensure_dir_exist(save_file_path)
    self.save_file_name = os.path.join(save_file_path,'cache.json')
    print('cache path', self.save_file_name)

  def set(self,k,v,ex):
    item = CacheKeyItem(v, ex)
    self.key_dict[k] = item


  def get(self,k):
    item = self.key_dict.get(k)
    if item is None:
      return None
    # elif item.expire <= int(time.time()):
    #   self.key_dict.pop(k)
    #   return None
    else:
      return item.data

  def remove(self,*args):
    for key in args:
      self.key_dict.pop(key)

  async def run_poll(self):
    while self.run:
      for k,v in self.key_dict.items():
        v.ttl -= self.polling_time
        if v.ttl < 1:
          self.key_dict.pop(k)
      await asyncio.sleep(self.polling_time)
      # print('cache run pull')

  async def start(self):
    self.load()
    loop = asyncio.get_running_loop()
    self.run = True
    self.task = loop.create_task(self.run_poll())
    return self.exit


  def load(self):
    data = read_json_file(self.save_file_name)
    if data is not None:
      data = {k:CacheKeyItem(v.get('v'), v.get('ex')) for k,v in data.items()}
      self.key_dict = data

  def exit(self):
    data = {k:v.to_dict() for k,v in self.key_dict.items()}
    write_json_file(self.save_file_name,data)