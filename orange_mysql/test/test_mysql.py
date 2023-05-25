from orange_mysql import pymysql
from orange_mysql.pymysql import OperationalError

db_config = {
  "host": 'localhost',
  "port": 3306,
  "user": 'root',
  "password": 'silviscene2023',
  "database": 'yyjc_dev',
  "charset": 'utf8'
}

def test():

  try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('select * from admin_user')
    result = cursor.fetchall()
    for row in result:
      print(row)
    cursor.close()
    conn.close()

  except pymysql.OperationalError as e:
    print(e)


test()

  # sql = 'select * from userinfo where name %s and pwd-%s:# 帮我拼接字符串的S0L语句,并且去数据库执行ret = cursor.execute(sql, [namepwdl])# 3.关闭
  # cursor.closeC
  # conn.close(
  # if ret:
  # print("登陆成功!")
  # else:
  # print("登录失败")