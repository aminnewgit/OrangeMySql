import datetime
from orange_kit.model import VoBase, VoField
from orange_kit.json import json_dumps,json_loads


from .aiomysql.pool import Pool
from .init import get_sql_pool
from .utils import get_values_placeholder,orange_sql_log
from .dto import Page


class SqlWhereBuilder:

  __slots__ = ("_where_sql_list","_where_param_list")

  def __init__(self):
    self._where_sql_list = []
    self._where_param_list = []

  def where_sql(self,sql: str, value_list=None, enable=True):
    if enable is True:
      self._where_sql_list.append(sql)
      if value_list is not None:
        self._where_param_list.extend(value_list)

  def eq(self,field: str, value, enable=True):
    """等于"""
    if enable is True:
      self._where_sql_list.append(f"(`{field}` = %s)")
      self.__after_add_where(value)
    return self

  def gt(self,field: str, value, enable=True):
    """等于"""
    if enable is True:
      self._where_sql_list.append(f"(`{field}` > %s)")
      self.__after_add_where(value)
    return self

  def lt(self,field: str, value, enable=True):
    """小于"""
    if enable is True:
      self._where_sql_list.append(f"(`{field}` < %s)")
      self.__after_add_where(value)
    return self

  def like(self, field: str, value, enable=True):
    """模糊查询"""
    if enable is True:
      self._where_sql_list.append(f"(`{field}` like '%%{value}%%') ")
      self._where_sql_list.append("AND")
      # self.__after_add_where(value)
    return self

  def in_(self, field: str, value_range, enable=True):
    if enable:
      placeholder = get_values_placeholder(len(value_range))
      sql = f" (((`{field}`) in ({placeholder})))"
      self._where_sql_list.append(sql)
      self._where_sql_list.append("AND")
      self._where_param_list.extend(value_range)
    return self

  def or_(self):
    """或"""
    self._where_sql_list.pop()
    self._where_param_list.append("OR")
    return self

  def __after_add_where(self, value):
    self._where_param_list.append(value)
    self._where_sql_list.append("AND")

  def _build_where(self):
    return  " ".join(self._where_sql_list[:-1])

class MySqlQuery(SqlWhereBuilder):

  __slots__ = (
    "__pool", "__table_name", "__all_select_str",
    "__select_str", "__order_str", "__select_field_list",
    "__entity"
  )
  def __init__(self, table_name,all_fields_str,pool,entity):
    super().__init__()
    self.__pool:Pool = pool
    self.__table_name = table_name
    self.__all_select_str = all_fields_str
    self.__select_str = None
    self.__order_str = None
    self.__select_field_list = None
    self.__entity: VoBase = entity


  # 联表查询 结果映射  # def left_join(self,sql):  #   pass

  def select(self,*args):
    """筛选字段"""
    if len(args) == 0: return

    field_dict = self.__entity.__field_dict__
    select_field_list = []
    for field_name in args:
      field = field_dict.get(field_name)
      if field is None:
        raise AttributeError(f"select field error! {field_name} not in entity")
      select_field_list.append(field)
    self.__select_field_list = select_field_list
    self.__select_str = ",".join(args)
    return self

  def order(self,field):
    """正序"""
    self.__order_str = f"ORDER BY `{field}`"
    return self

  def order_desc(self,field):
    """倒叙"""
    # todo 多条条件排序优化
    # args = [f"`{field}`" for field in args]
    self.__order_str = f"ORDER BY `{field}` DESC, id DESC"
    return self

  def __build_sql(self):
    sql = []
    if self.__select_str is not None:
      sql.append(f"SELECT {self.__select_str}")
    else:
      sql.append(f"SELECT {self.__all_select_str}")
      self.__select_field_list = self.__entity.__field_list__
    sql.append(f"FROM {self.__table_name}")
    where_str = self._build_where()
    if where_str.strip() != "":
      sql.append(f"WHERE {where_str}")
    if self.__order_str is not None:
      sql.append(self.__order_str)
    return sql

  def __build_count_sql(self):
    sql = [
      f"SELECT  count(*)",
      f"FROM {self.__table_name}"
    ]
    where_str = self._build_where()
    if where_str.strip() != "":
      sql.append(f"WHERE {where_str}")
    sql = "\n".join(sql)
    return sql

  @staticmethod
  def __get_val_from_db_return(field:VoField,val):
    if field.db_map_json is True:
      val = json_loads(val)
    elif field.type == bool:
      val = val == b'\x01'
    return val

  def __create_out_obj(self, data, out_type):
    out = out_type()
    for index, field in enumerate(self.__select_field_list):
      val = data[index]
      val = self.__get_val_from_db_return(field,val)
      object.__setattr__(out,field.name,val)
    return out

  def __create_out_dict(self, data):
    out = dict()
    for index, field in enumerate(self.__select_field_list):
      val = data[index]
      val = self.__get_val_from_db_return(field, val)
      out[field.name] = val
    return out

  async def __get_first(self):
    orange_sql_log.debug.split_line()
    sql = self.__build_sql()
    sql = "\n".join(sql)
    async with self.__pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(sql, self._where_param_list)
        r = await cur.fetchone()
        orange_sql_log.debug(r)
        return r

  async def __get_list(self):
    orange_sql_log.debug.print_split()
    sql = self.__build_sql()
    sql = "\n".join(sql)
    async with self.__pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(sql, self._where_param_list)
        r = await cur.fetchall()
        orange_sql_log.debug.list(r)
        return r

  def __select_from_dto(self,dto_type):
    out_fields = dto_type.__field_name_list__
    # 可以在vo中增加个映射的 功能
    out_fields = [field for field in out_fields
                  if field in self.__entity.__field_name_list__]
    self.select(*out_fields)

  def __handler_out_type(self,out_type):
    if out_type is None:
      out_type = self.__entity
    elif issubclass(out_type, VoBase):
      self.__select_from_dto(out_type)
    return out_type

  async def get_first(self,out_type=None):
    out_type = self.__handler_out_type(out_type)
    data = await self.__get_first()
    if data is None: return
    elif out_type == tuple:
      return data
    elif out_type == dict:
      return self.__create_out_dict(data)
    else:
      return self.__create_out_obj(data,out_type)

  def __out__list(self,data_list,out_type):
    if out_type == tuple:
      return data_list
    elif out_type == dict:
      return [self.__create_out_dict(data) for data in data_list]
    else:
      return [self.__create_out_obj(data, out_type) for data in data_list]

  async def get_list(self,out_type=None):
    out_type = self.__handler_out_type(out_type)
    data_list = await self.__get_list()
    return self.__out__list(data_list,out_type)

  async def count(self):
    orange_sql_log.debug.split_line()
    count_sql = self.__build_count_sql()
    async with self.__pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(count_sql, self._where_param_list)
        r = await cur.fetchone()
        orange_sql_log.debug(r)
        return r[0]

  async def __page(self, index:int, size: int):
    orange_sql_log.debug.print_split()
    count_sql = self.__build_count_sql()
    async with self.__pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(count_sql, self._where_param_list)
        r = await cur.fetchone()
        total = r[0]
        orange_sql_log.debug("total", total)
        if total == 0:
          return [],0
        # todo 分页优化
        orange_sql_log.debug.print_split()
        sql = self.__build_sql()
        sql.append(f"limit {size*(index-1)},{size}")
        # sql.append("limit 1 10")
        sql = "\n".join(sql)
        await cur.execute(sql, self._where_param_list)
        r = await cur.fetchall()
        orange_sql_log.debug.print_split()
        orange_sql_log.debug.list(r)
        return r,total

  async def page(self,page:Page,out_type=None):
    """分页查询"""
    out_type = self.__handler_out_type(out_type)
    out_list,total = await self.__page(page.index,page.size)
    page.total = total
    if total == 0: return []
    return self.__out__list(out_list, out_type)

class MysqlUpdate(SqlWhereBuilder):

  __slots__ = ("__pool","__table_name","__entity",
               "__update_sql_list","__update_param_list","__fill_time")

  def __init__(self, table_name, pool, entity, fill_time):
    super().__init__()
    self.__pool: Pool = pool
    self.__table_name = table_name
    self.__entity: VoBase = entity
    self.__fill_time = fill_time

    self.__update_sql_list = []
    self.__update_param_list = []

  def set(self,field:str,value,enable=True):
    """
    UPDATE `test_song` SET `title` = ?p_0, `singer` = ?p_1, `ct` = now(3)
    WHERE (`id` = 1)
    """
    if enable is False: return
    self.__update_sql_list.append(f"`{field}`=%s")
    self.__update_param_list.append(value)

  def set_sql(self,sql,enable=True):
    if enable is False: return
    self.__update_sql_list.append(sql)

  def app_params(self,*args):
    self.__update_param_list.extend(args)

  def __build_sql_str(self):

    if self.__fill_time is True:
      self.set("ut",datetime.datetime.now())

    if len(self.__update_sql_list) == 0:
      raise AttributeError("no update field add")
    sql = [
      f"UPDATE `{self.__table_name}`",
      f"SET {', '.join(self.__update_sql_list)}"
    ]
    where_str = self._build_where()
    if where_str.strip() == "":
      raise AttributeError("没有where条件 更新不安全")
    sql.append(f"WHERE {where_str}")
    sql = "\n".join(sql)

    param_list = self.__update_param_list + self._where_param_list

    return sql,param_list

  async def execute(self)->int:
    orange_sql_log.debug.split_line()
    sql,param_list = self.__build_sql_str()
    async with self.__pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(sql, param_list)
        await conn.commit()
        affected_num = cur.rowcount
        orange_sql_log.debug("affected_num", affected_num)
        return affected_num

class BaseRepo:

  __slots__ = (
    "__table_name","__pool",
    "__entity","__all_fields_str",
    "__insert_sql","__field_list_no_id"
  )

  def __init__(self, table_name,entity: VoBase):
    self.__table_name = table_name
    self.__pool = get_sql_pool()
    self.__entity = entity
    # 生成insert sql 语句
    self.__build_insert_sql()
    self.__build_all_fields_str()


  def __build_all_fields_str(self):
    self.__all_fields_str = ','.join(self.__entity.__field_name_list__)

  def __build_insert_sql(self):
    field_name_list = [i for i in self.__entity.__field_name_list__ if i != "id"]
    placeholder = get_values_placeholder(field_name_list.__len__())
    # noinspection SqlNoDataSourceInspection
    self.__insert_sql = f"insert into {self.__table_name} ({','.join(field_name_list)}) VALUES({placeholder})"
    self.__field_list_no_id: list[VoField] = [i for i in self.__entity.__field_list__ if i.name != "id"]

  async def insert(self,obj,fill_time=True):
    if fill_time is True:
      now = datetime.datetime.now()
      obj.ut = now
      obj.ct = now
    orange_sql_log.debug.print_split()
    async with self.__pool.acquire() as conn:
      async with conn.cursor() as cur:
        d_dict = obj.__dict__
        d_list = []
        for field in self.__field_list_no_id:
          d = d_dict.get(field.name,None)
          print(field.name,d,field.db_map_json)
          if field.db_map_json is True:
            d = json_dumps(d)
          d_list.append(d)
        await cur.execute(self.__insert_sql,d_list)
        obj.id = cur.lastrowid
        await conn.commit()




  def query(self)->MySqlQuery:
    return MySqlQuery(self.__table_name,
                      self.__all_fields_str,
                      self.__pool,
                      self.__entity)

  def update(self,fill_time=True)->MysqlUpdate:
    return MysqlUpdate(
      self.__table_name,
      self.__pool,
      self.__entity,
      fill_time)

