"""
信息技术技巧大全推荐系统
配置文件
"""
# 基本设置 ----------------------------------------------------
# 是否输出运行信息
VERBOSE = True

# 推荐物品数
RECOMMEND_NUM = 5
# 推荐新物品数
RECOMMEND_NEW_NUM = 3

# 推荐结果中推荐度的最大值和最小值
MAX_SCORE = 100
MIN_SCORE = 80

# 设置距今几天的物品为新物品
DAY_NUM = 30

# 推荐指数的参数
# 下载次数
MAX_DOWNLOAD_COUNT = 10
DOWNLOAD_COUNT_WEIGHT = 0.3
# 浏览次数
MAX_BROWSE_COUNT = 10
BROWSE_COUNT_WEIGHT = 0.3
# 评星等级
STAR_WEIGHT = 0.4

# 保存推荐结果的数据库表名
RESULT_TABLE = 'recommend_infor_tech'
ALLDATA_TABLE = 'alldata_recommend_infor_tech'
STAY_TABLE = 'stay_recommend_infor_tech'

# 读取数据时需要用到的数据库表名 -----------------------------
# 用户—信息技术技巧浏览
USER_ITEM_BD_TABLE = 'ts508'

# 项目-用户信息表
USER_INFO_TABLE = 'ts501'

# 信息技术技巧大全信息表
INFO_TECH_MSG_TABLE = 'ts507'


# SQL语句 ----------------------------------------------------
# 用户ID-物品ID
user_item_data_sql = """SELECT userid, resourceid
                        FROM {user_item_bd_table}
                        GROUP BY userid, resourceid"""\
    .format(user_item_bd_table=USER_ITEM_BD_TABLE)

# 物品ID-内容
item_msg_sql = """SELECT shareid, key_type 
                  FROM {info_tech_msg_table} 
                  GROUP BY shareid""".format(info_tech_msg_table=INFO_TECH_MSG_TABLE)


# 用户信息
user_info_sql = """SELECT userid, projectid, age, gender, schoolstagecode, subjectcode FROM {user_info}"""\
    .format(user_info=USER_INFO_TABLE)

# 物品ID-推荐度
item_score_sql = """SELECT shareid, ({download_weight}*t.d/{max_download_count}+{browse_weight}*t.b/{max_browse_count}+{star_weight}*t.s/5) AS score
                    FROM (
                        SELECT shareid, 
                        IF(downloadcount > {max_download_count}, {max_download_count}, downloadcount) AS d, 
                        IF(browsecount > {max_browse_count}, {max_browse_count}, browsecount) AS b,  
                        IF(star > 5, 5, star) AS s
                        FROM (
                        SELECT shareid, SUM(downloadcount) as downloadcount, SUM(browsecount) as browsecount, Max(star) as star
                        FROM {info_tech_msg_table}
                        GROUP BY shareid) AS t1 ) AS t"""\
    .format(info_tech_msg_table=INFO_TECH_MSG_TABLE,
            max_download_count=MAX_DOWNLOAD_COUNT, download_weight=DOWNLOAD_COUNT_WEIGHT,
            max_browse_count=MAX_BROWSE_COUNT, browse_weight=BROWSE_COUNT_WEIGHT,
            star_weight=STAR_WEIGHT)

# 新物品ID
import datetime
new_date = datetime.datetime.now() + datetime.timedelta(days=-DAY_NUM)
new_date = '"' + new_date.strftime('%Y-%m-%d') + '"'
new_item_id_sql = """SELECT shareid
                     FROM {info_tech_msg_table}
                     WHERE createtime > {date} 
                     GROUP BY shareid""".format(info_tech_msg_table=INFO_TECH_MSG_TABLE, date=new_date)

# 项目-关闭时间表
project_id_close_sql = "SELECT DISTINCT projectid, close_date FROM {user_info}".format(user_info=USER_INFO_TABLE)
