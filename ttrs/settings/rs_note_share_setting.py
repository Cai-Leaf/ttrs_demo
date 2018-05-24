"""
研修日志推荐系统
配置文件
"""
# 基本设置 ----------------------------------------------------
# 是否输出运行信息
VERBOSE = True

# 内容模型推荐物品数
CONTENT_RECOMMEND_NUM = 5
# 协同过滤模型推荐物品数
CF_RECOMMEND_NUM = 5

# 推荐结果中推荐度的最大值和最小值
MAX_SCORE = 100
MIN_SCORE = 80

# 推荐指数的参数
# 评论次数
MAX_COMMENT_COUNT = 10
COMMENT_COUNT_WEIGHT = 0.1
# 浏览次数
MAX_BROWSE_COUNT = 10
BROWSE_COUNT_WEIGHT = 0.1
# 点赞次数
MAX_GOOD_COUNT = 10
GOOD_COUNT_WEIGHT = 0.1
# 有效天数
DAY_NUM = 30
DAY_NUM_WEIGHT = 0.3
# 评星等级
STAR_WEIGHT = 0.4

# 保存推荐结果的数据库表名
RESULT_TABLE = 'recommend_note_share'
ALLDATA_TABLE = 'alldata_recommend_note_share'
STAY_TABLE = 'stay_recommend_note_share'

# 读取数据时需要用到的数据库表名 -----------------------------
# 项目-用户信息表
USER_INFO_TABLE = 'ts501'

# 研修日志行为信息表
ITEM_MSG_TABEL = 'ts505'

# 研修日志-用户浏览
USER_ITEM_TABLE = 'ts506'


# SQL语句 ----------------------------------------------------
# 用户信息
user_info_sql = """SELECT userid, projectid, schoolstagecode, subjectcode FROM {user_info}"""\
    .format(user_info=USER_INFO_TABLE)

# 用户ID-项目ID-物品ID
user_item_sql = """SELECT userid, projectid, blogid
                   FROM {user_item_table}
                   WHERE projectid IN (SELECT DISTINCT projectid FROM {user_info_table})
                   GROUP BY userid, blogid"""\
    .format(user_item_table=USER_ITEM_TABLE, user_info_table=USER_INFO_TABLE)

# 用户ID-项目ID-最近浏览物品ID
user_near_item_sql = """SELECT userid, projectid, blogid
                        FROM (
                            SELECT *
                            FROM {user_item_table}
                            WHERE projectid IN (SELECT DISTINCT projectid FROM {user_info_table})
                            GROUP BY userid, blogid
                        ) AS a
                        WHERE (
                            SELECT COUNT(createtime)
                            FROM (
                                SELECT *
                                FROM {user_item_table}
                                WHERE projectid IN (SELECT DISTINCT projectid FROM {user_info_table})
                                GROUP BY userid, blogid
                            ) as b
                            WHERE b.userid = a.userid AND b.projectid = a.projectid AND b.createtime > a.createtime
                        ) < {browse_num} 
                        ORDER BY userid, projectid"""\
    .format(user_item_table=USER_ITEM_TABLE, user_info_table=USER_INFO_TABLE, browse_num=CONTENT_RECOMMEND_NUM)

# 物品ID-项目ID-内容
item_content_sql = """SELECT DISTINCT blogid, projectid, content
                      FROM {item_msg_table}
                      WHERE projectid IN (SELECT DISTINCT projectid FROM {user_info_table})"""\
    .format(item_msg_table=ITEM_MSG_TABEL, user_info_table=USER_INFO_TABLE)

# 物品ID-推荐度
import datetime
date = '"' + datetime.datetime.now().strftime('%Y-%m-%d') + '"'
item_score_sql = """SELECT blogid, projectid, ({comment_count_weight}*t.p/{max_comment_count}+
                                                {browse_weight}*t.b/{max_browse_count}+
                                                {good_weight}*t.z/{max_good_count}+
                                                {star_weight}*t.s/5+
                                                {day_num_weight}*{day_num}/d) AS score
                    FROM (
                            SELECT blogid, projectid,
                            IF(pl_count > {max_comment_count}, {max_comment_count}, pl_count) AS p, 
                            IF(ll_count > {max_browse_count}, {max_browse_count}, ll_count) AS b,
                            IF(dz_count > {max_good_count}, {max_good_count}, dz_count) AS z,    
                            IF(star > 5, 5, star) AS s,
                            IF(createtime < {day_num}, {day_num}, createtime) AS d
                            FROM (
                                SELECT blogid, projectid,
                                                SUM(ll_count) as ll_count, 
                                                SUM(dz_count) as dz_count, 
                                                SUM(pl_count) as pl_count, 
                                                MAX(star) as star, 
                                                DATEDIFF({date}, MAX(createtime)) as createtime
                                FROM {item_msg_table}
                                WHERE projectid IN (SELECT DISTINCT projectid FROM {user_info_table})
                                GROUP BY blogid
                            ) AS t2
                    ) AS t"""\
    .format(item_msg_table=ITEM_MSG_TABEL, user_info_table=USER_INFO_TABLE,
            max_comment_count=MAX_COMMENT_COUNT, comment_count_weight=COMMENT_COUNT_WEIGHT,
            max_browse_count=MAX_BROWSE_COUNT, browse_weight=BROWSE_COUNT_WEIGHT,
            max_good_count=MAX_GOOD_COUNT, good_weight=GOOD_COUNT_WEIGHT,
            day_num=DAY_NUM, day_num_weight=DAY_NUM_WEIGHT,
            star_weight=STAR_WEIGHT, date=date)

# 项目-关闭时间表
project_id_close_sql = "SELECT DISTINCT projectid, project_endtime FROM {user_info}".format(user_info=USER_INFO_TABLE)

