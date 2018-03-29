import MySQLdb
import pandas as pd
import time
from ttrs.recommend_note_share.model import *

# 打开数据库连接
db = MySQLdb.connect(host='localhost', user='root', password='123456', database='tt_nov', charset='utf8')
cursor = db.cursor()

try:
    # 执行SQL语句
    sql = """SELECT blogid, projectid, content
            FROM ts505
            WHERE projectid in (
            SELECT DISTINCT projectid
            FROM ts501
            ) """
    cursor.execute(sql)
    # 获取所有记录列表
    db_data = cursor.fetchall()
    data = pd.DataFrame(list(db_data), columns=['iid', 'pid', 'content'])
except AssertionError:
    raise AssertionError('构造Dataframe时出错')
except:
    raise IOError('读取数据库出错')
# 关闭数据库连接
db.close()
model = ContentSimilarityModel()
start = time.time()
model.fit(data)
print(time.time()-start)






