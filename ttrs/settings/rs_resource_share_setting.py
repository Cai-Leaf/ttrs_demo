"""
资源推荐系统
配置文件
"""
# 基本设置 ----------------------------------------------------
# 是否输出运行信息
VERBOSE = True

# 类别模型推荐物品数
MODEL1_RECOMMEND_NUM = 3
# 协同过滤模型推荐物品数
MODEL2_RECOMMEND_NUM = 3

# 推荐结果中推荐度的最大值和最小值
MAX_SCORE = 100
MIN_SCORE = 80

# 推荐指数的参数
# 下载次数
MAX_DOWNLOAD_COUNT = 10
DOWNLOAD_COUNT_WEIGHT = 0.2
# 浏览次数
MAX_BROWSE_COUNT = 10
BROWSE_COUNT_WEIGHT = 0.2
# 点赞次数
MAX_GOOD_COUNT = 10
GOOD_COUNT_WEIGHT = 0.2
# 评星等级
STAR_WEIGHT = 0.4

# 保存推荐结果的数据库表名
RESULT_TABLE = 'recommend_resource_share'
ALLDATA_TABLE = 'alldata_recommend_resource_share'
STAY_TABLE = 'stay_recommend_resource_share'

# 读取数据时需要用到的数据库表名 -----------------------------
# 项目-用户信息表
USER_INFO_TABLE = 'ts501'

# 资源分享信息表
ITEM_MSG_TABEL = 'ts511'

# 资源-用户行为
USER_ITEM_TABLE = 'ts512'


# SQL语句 ----------------------------------------------------
# 用户ID-物品ID-项目ID
user_item_sql = """SELECT userid, resourceid, projectid
                   FROM {user_item_table}
                   WHERE projectid IN (SELECT DISTINCT projectid FROM {user_info_table})
                   GROUP BY userid, resourceid, projectid"""\
    .format(user_item_table=USER_ITEM_TABLE, user_info_table=USER_INFO_TABLE)

# 用户信息
user_info_sql = """SELECT userid, projectid, age, gender, schoolstagecode, subjectcode FROM {user_info}"""\
    .format(user_info=USER_INFO_TABLE)

# 物品ID-项目ID-资源类型-推荐度
item_score_sql = """SELECT resourceid, projectid, resourcetype, ({download_weight}*t.d/{max_download_count}+{browse_weight}*t.b/{max_browse_count}+{good_weight}*t.z/{max_good_count}+{star_weight}*t.s/5) AS score
                    FROM (
                        SELECT resourceid, projectid, resourcetype,
                        IF(xz_count > {max_download_count}, {max_download_count}, xz_count) AS d, 
                        IF(ll_count > {max_browse_count}, {max_browse_count}, ll_count) AS b,
                        IF(dz_count > {max_good_count}, {max_good_count}, dz_count) AS z,    
                        IF(pl_count > 5, 5, pl_count) AS s
                        FROM (
                                SELECT resourceid, projectid, resourcetype, SUM(xz_count) as xz_count, SUM(ll_count) as ll_count, SUM(dz_count) as dz_count, MAX(pl_count) as pl_count
                                FROM {item_msg_table}
                                GROUP BY resourceid, projectid
                              ) AS t2
                        WHERE projectid IN (SELECT DISTINCT projectid FROM {user_info_table})
                    ) AS t"""\
    .format(item_msg_table=ITEM_MSG_TABEL, user_info_table=USER_INFO_TABLE,
            max_download_count=MAX_DOWNLOAD_COUNT, download_weight=DOWNLOAD_COUNT_WEIGHT,
            max_browse_count=MAX_BROWSE_COUNT, browse_weight=BROWSE_COUNT_WEIGHT,
            max_good_count=MAX_BROWSE_COUNT, good_weight=BROWSE_COUNT_WEIGHT,
            star_weight=STAR_WEIGHT)

