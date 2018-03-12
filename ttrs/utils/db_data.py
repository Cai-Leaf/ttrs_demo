import MySQLdb
import pandas as pd
from ..settings.db_setting import *
import time


# 读取数据库内容，并构造DataFrame
def read_db_to_df(sql, contain, info='', verbose=True):
    # 打开数据库连接
    db = MySQLdb.connect(host=R_HOST, user=R_USER, password=R_PASSWORD, database=R_DATABASE, charset=R_CHARSET)
    cursor = db.cursor()
    start = time.time()
    try:
        # 执行SQL语句
        cursor.execute(sql)
        # 获取所有记录列表
        db_data = cursor.fetchall()
        result = pd.DataFrame(list(db_data), columns=contain)
    except AssertionError:
        raise AssertionError('构造Dataframe时出错')
    except:
        raise IOError('读取数据库出错')
    # 关闭数据库连接
    db.close()
    if verbose:
        print(info, '数据读取完毕，用时',
              int((time.time() - start) // 60), '分',
              int((time.time() - start) % 60), '秒')
    return result


# 将数据存入数据库
def save_data_to_db(data, table_name, contain, is_truncate=False, verbose=True):
    if len(data) == 0:
        if verbose:
            print(table_name, "没有数据被写入数据库")
        return
    if len(contain) != len(data[0]):
        raise ValueError('字段个数与数据列数长度不符')
    db = MySQLdb.connect(host=W_HOST, user=W_USER, password=W_PASSWORD, database=W_DATABASE, charset=W_CHARSET)
    bach_size = MAX_SAVE_DATA_BACH_SIZE
    bach_num = round(len(data) / bach_size)
    if bach_num == 0:
        bach_num = 1
    cursor = db.cursor()
    start = time.time()
    try:
        # 执行sql语句
        if is_truncate:
            cursor.execute('TRUNCATE TABLE '+table_name)
        for i in range(bach_num):
            sql_1 = 'INSERT INTO ' + table_name + ' (' + ','.join(contain) + ') ' + 'VALUES ' + \
                    ','.join(['(' + ','.join(['\'' + str(i) + '\'' for i in item]) + ')' for item in data[i*bach_size:(i+1)*bach_size]])
            cursor.execute(sql_1)
        # 提交到数据库执行
        db.commit()
    except:
        # 回滚数据
        db.rollback()
        raise IOError('写数据库出错')
    finally:
        db.close()
    if verbose:
        print(table_name, '数据写入完毕，用时',
              int((time.time() - start) // 60), '分',
              int((time.time() - start) % 60), '秒')
    return


# 根据userid删除数据库的内容
def delete_data_with_userid(uid_list, table_name, verbose=True):
    if len(uid_list) == 0:
        if verbose:
            print(table_name, "没有删除任何数据")
        return
    db = MySQLdb.connect(host=W_HOST, user=W_USER, password=W_PASSWORD, database=W_DATABASE, charset=W_CHARSET)
    bach_size = MAX_SAVE_DATA_BACH_SIZE
    bach_num = round(len(uid_list) / bach_size)
    if bach_num == 0:
        bach_num = 1
    cursor = db.cursor()
    start = time.time()
    try:
        # 执行sql语句
        for i in range(bach_num):
            sql = 'DELETE FROM ' + table_name + ' WHERE userid IN (' + ','.join([str(i) for i in uid_list[i*bach_size:(i+1)*bach_size]]) + ')'
            cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except:
        # 回滚数据
        db.rollback()
        raise IOError('写数据库出错')
    finally:
        db.close()
    if verbose:
        print(table_name, '数据删除完毕，用时',
              int((time.time() - start) // 60), '分',
              int((time.time() - start) % 60), '秒')
    return


def delete_data_with_userid_projectid(uid_pid_list, table_name, verbose=True):
    if len(uid_pid_list) == 0:
        if verbose:
            print(table_name, "没有删除任何数据")
        return
    db = MySQLdb.connect(host=W_HOST, user=W_USER, password=W_PASSWORD, database=W_DATABASE, charset=W_CHARSET)
    cursor = db.cursor()
    start = time.time()
    print(len(uid_pid_list))
    try:
        # 执行sql语句
        for uid, pid in uid_pid_list:
            sql = 'DELETE FROM {table_name}  WHERE userid = {uid} AND projectid = {pid}'.\
                format(table_name=table_name, uid=uid, pid=pid)
            cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except:
        # 回滚数据
        db.rollback()
        raise IOError('写数据库出错')
    finally:
        db.close()
    if verbose:
        print(table_name, '数据删除完毕，用时',
              int((time.time() - start) // 60), '分',
              int((time.time() - start) % 60), '秒')
    return

