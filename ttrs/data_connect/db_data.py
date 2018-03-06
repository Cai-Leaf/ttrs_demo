import MySQLdb
import pandas as pd
from ..settings.db_setting import *
import time
import threading
from multiprocessing import Process, Pool


# 读取数据库内容，并构造DataFrame
def read_db_to_df(sql, contain, info=''):
    # 打开数据库连接
    db = MySQLdb.connect(host=HOST,
                         user=USER,
                         password=PASSWORD,
                         database=DATABASE,
                         charset=CHARSET)
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
    print(info+'数据读取完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')
    return result


# 将数据存入数据库
def save_data_to_db(data, table_name, contain, is_truncate=False, info='', verbose=True):
    if len(data) == 0:
        print("没有数据被写入数据库")
        return
    if len(contain) != len(data[0]):
        raise ValueError('字段个数与数据列数长度不符')
    db = MySQLdb.connect(host=HOST,
                         user=USER,
                         password=PASSWORD,
                         database=DATABASE,
                         charset=CHARSET)
    cursor = db.cursor()
    start = time.time()
    try:
        # 执行sql语句
        if is_truncate:
            cursor.execute('TRUNCATE TABLE '+table_name)
        sql = 'INSERT INTO ' + table_name + ' (' + ','.join(contain) + ') ' + 'VALUES ' + \
              ','.join(['(' + ','.join(['\'' + str(i) + '\'' for i in item]) + ')' for item in data])
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except:
        # 回滚数据
        db.rollback()
        raise IOError('写数据库出错')
    if verbose:
        print(info + '数据写入完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')
    return


# 将数据存入数据库
def save_big_data_to_db(data, table_name, contain, is_truncate=False, info=''):
    if len(data) == 0:
        print("没有数据被写入数据库")
        return
    if len(contain) != len(data[0]):
        raise ValueError('字段个数与数据列数长度不符')
    db = MySQLdb.connect(host=HOST,
                         user=USER,
                         password=PASSWORD,
                         database=DATABASE,
                         charset=CHARSET)
    bach_size = MAX_SAVE_DATA_BACH_SIZE
    bach_num = round(len(data) / bach_size)
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
    print(info + '数据写入完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')
    return


def save_big_data_to_db_multiprocessing(data, table_name, contain, is_truncate=False, info='', verbose=True):
    if len(data) == 0:
        print("没有数据被写入数据库")
        return
    if len(contain) != len(data[0]):
        raise ValueError('字段个数与数据列数长度不符')
    bach_size = MAX_SAVE_DATA_BACH_SIZE
    bach_num = round(len(data)/bach_size)
    start = time.time()
    # 先把第一批数据存入数据库
    save_data_to_db(data[:bach_size], table_name, contain, is_truncate, verbose=True)
    # 多进程存入后续数据
    process_pool = Pool(16)
    for i in range(1, bach_num):
        process_pool.apply_async(func=save_data_to_db,
                                 args=(data[i*bach_size:(i+1)*bach_size], table_name, contain, False, '', True))
    process_pool.close()
    process_pool.join()
    if verbose:
        print(info + '数据写入完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')
    return
