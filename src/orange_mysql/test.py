import asyncio
import datetime

from orange_kit.json import json_dumps
from orange_kit.model import VoBase, VoField
from .base_repo import BaseRepo, QueryPage
from .init_tool import log



class YyjcTask(VoBase):
 id: int
 type: str              = VoField("str vido/rtsp 视频类型")
 input: str             = VoField("str 输入地址 视频地址或流地址")
 eval_interval: int     = VoField("int 报警间隔")
 min_score: int         = VoField("最小得分")
 status: str            = VoField("状态")
 alarm_class_list:list[str]      = VoField("报警类型列表",db_map_json=True)
 start_time: datetime.datetime   = VoField("开始时间")
 ut: datetime.datetime  = VoField("更新时间")
 ct: datetime.datetime  = VoField("创建时间")
 is_del: bool           = VoField("软删除标志",default=False)


def test_vo ():
 # debug_log_dict(YyjcTask.__dict__)
 data = {
  'type': 'video',
  'input': 'Bolt.mp4',
  'alarmClassList': ['person'],
  'evalInterval': 10,
  'score': 0.5
 }
 task = YyjcTask()
 task.__init_by_camel_case__(data)
 print(task.input)
 print(YyjcTask.input)
 print(json_dumps(task))

# test_vo()

class TaskDto(VoBase):
 id: int
 type: str              = VoField("str vido/rtsp 视频类型")
 input: str             = VoField("str 输入地址 视频地址或流地址")
 eval_interval: int     = VoField("int 报警间隔")


class TaskRepo(BaseRepo):
 def __init__(self, ):
  super().__init__("eval_task", YyjcTask)


async def insert_test():
 repo = TaskRepo()
 data = {
  'type': 'video',
  'input': 'Bolt.mp4',
  'alarmClassList': ['person'],
  'evalInterval': 10,
  'score': 0.5
 }
 task = YyjcTask(data)
 task.start_time = datetime.datetime.now()
 await repo.insert(task)


async def query_test():
 repo = TaskRepo()
 query = repo.query()
 query.gt("eval_interval",3)
 query.lt("eval_interval", 15)
 query.order_desc("start_time")
 # task:list[YyjcTask] = await query.get_list() # 获取列表
 # task:YyjcTask = await query.get_first() # 输出entity
 # task = await query.get_first(tuple)     # 输出原始元组数据
 # task = await query.get_first(dict)      # 输出dict
 # task:TaskDto = await query.get_first(TaskDto)  # 根据指定对象输出, 并做字段裁剪
 # total = await query.count() # 统计数量

 # task:list[YyjcTask], total:int = await query.page(1,10) # 获取分页
 page = QueryPage(1,3)
 task_list:list[YyjcTask] = await query.page(page) # 获取分页
 task_list: list[YyjcTask] = await query.page(page,TaskDto)  # 获取分页

 log.debug(task_list)

 # print(json_dumps(task))

async def update_test():
 repo = TaskRepo()
 update = repo.update()
 update.set(YyjcTask.status, "stop")
 update.eq(YyjcTask.id,65)
 await update.execute()


async def test_mysql():
  await insert_test()
  # await query_test()
  # await update_test()
  await asyncio.sleep(0.1)






