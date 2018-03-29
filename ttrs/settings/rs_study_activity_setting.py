"""
研修活动推荐
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

# 设置距今几天的活动参与信息需要纳入计算范围
CORRECT_DAY_NUM = 30

# 设置距今几天的物品为新物品
NEW_DAY_NUM = 10

# 保存研修活动推荐结果的数据库表名
RESULT_TABLE = 'recommend_study_activity'
ALLDATA_TABLE = 'alldata_recommend_study_activity'
STAY_TABLE = 'stay_recommend_study_activity'

# 读取数据时需要用到的数据库表名 -----------------------------
# 项目-用户信息表
USER_INFO_TABLE = 'ts501'

# 研修活动基本信息表
ACTIVITY_MSG_TABLE = 'ts509'

# 研修活动-用户参与信息
USER_ACTIVITY_TABLE = 'ts510'


# SQL语句 ----------------------------------------------------
import datetime

# 用户-活动参与信息
date = datetime.datetime.now() + datetime.timedelta(days=-CORRECT_DAY_NUM)
date = '"' + date.strftime('%Y-%m-%d') + '"'
user_activity_sql = """SELECT userid, projectid, activitiesid
                       FROM {user_activity_table}
                       WHERE minjointime > {date} """.format(user_activity_table=USER_ACTIVITY_TABLE, date=date)

# 用户信息
user_info_sql = """SELECT userid, projectid, schoolstagecode, subjectcode FROM {user_info}"""\
    .format(user_info=USER_INFO_TABLE)

# 候选物品列表
now_date = '"' + datetime.datetime.now().strftime('%Y-%m-%d') + '"'
new_date = datetime.datetime.now() + datetime.timedelta(days=-NEW_DAY_NUM)
new_date = '"' + new_date.strftime('%Y-%m-%d') + '"'
item_candidate_sql = """SELECT activiesid, projectid, schoolstagecode, subjectcode
                        FROM {activity_msg_table}
                        WHERE enddate > {now} AND begindate < {new_date} """\
    .format(activity_msg_table=ACTIVITY_MSG_TABLE, now=now_date, new_date=new_date)

# 新物品列表
new_date = datetime.datetime.now() + datetime.timedelta(days=-NEW_DAY_NUM)
new_date = '"' + new_date.strftime('%Y-%m-%d') + '"'
new_item_sql = """SELECT activiesid, projectid, schoolstagecode, subjectcode
          FROM {activity_msg_table}
          WHERE begindate > {new_date} """\
    .format(activity_msg_table=ACTIVITY_MSG_TABLE,  new_date=new_date)

