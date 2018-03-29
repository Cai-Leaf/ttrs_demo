import re
import pandas as pd
import MySQLdb

file_object = open('data/ts505.csv', 'r', encoding='utf-8')
n = 0
content = []
for line in file_object:
    if n == 0:
        data = str(line)
        data = re.split(r";|\n", data)
        col_name = data[:-1]
    else:
        data = str(line)
        data = re.split(r";", data)
        ccc = "".join(data[5:-6])
        ccc = ccc.replace('"', "")
        ccc = ccc.replace("'", "")
        data = data[0:5]+[ccc]+data[-6:-1]+[data[-1][:-1]]
        if len(data) == 12 and len(data[-1]) == 10 and len(data[-2]) == 10 and len(data[3]) == 4:
            content.append(data)
    n += 1
file_object.close()
print(n)
print(len(content[222]))
print(len(col_name))
print(content[222])
print(col_name)


db = MySQLdb.connect(host='localhost', user='root', password='123456', database='tt_nov', charset='utf8')
bach_size = 10
bach_num = round(len(content) / bach_size)
if bach_num == 0:
    bach_num = 1
cursor = db.cursor()
try:
    # 执行sql语句
    for i in range(bach_num):
        sql_1 = 'INSERT INTO ' + 'ts505' + ' (' + ','.join(col_name) + ') ' + 'VALUES ' + \
                ','.join(['(' + ','.join(['"' + str(i) + '"' for i in item]) + ')' for item in
                          content[i * bach_size:(i + 1) * bach_size]])
        cursor.execute(sql_1)
    # 提交到数据库执行
    db.commit()
except:
    # 回滚数据
    db.rollback()
    print(sql_1)
    raise IOError('写数据库出错')
finally:
    db.close()

