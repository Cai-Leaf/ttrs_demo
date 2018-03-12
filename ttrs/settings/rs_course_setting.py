"""
选修课推荐系统
开放课程推荐系统
配置文件
"""
# 基本设置 ----------------------------------------------------
# 是否输出运行信息
VERBOSE = True

# 选修课推荐课程数
RECOMMEND_COURSE_NUM = 10

# 开放课推荐课程数
RECOMMEND_OPEN_COURSE_NUM = 10

# 推荐度的最大值和最小值
MAX_SCORE = 100
MIN_SCORE = 80

# 保存选修课推荐结果的数据库表名
COURSE_TABLE = 'recommend_optional_course'
ALLDATA_COURSE_TABLE = 'alldata_recommend_optional_course'
STAY_COURSE_TABLE = 'stay_recommend_optional_course'

# 保存开放课推荐结果的数据库表名
OPEN_COURSE_TABLE = 'recommend_open_course'
ALLDATA_OPEN_COURSE_TABLE = 'alldata_recommend_open_course'
STAY_OPEN_COURSE_TABLE = 'stay_recommend_open_course'

# 读取数据时需要用到的数据库表名 -----------------------------
# 表1.用户信息表
USER_INFO_TABLE = 'user_info'

# 表2.用户课程信息表
USER_COURSE_INFO_TABLE = 'ts502'

# 表6.项目—学习任务—选修课列表
PROJECT_ACTIVISE_COURSE = 'project_activies_course'


# SQL语句 ----------------------------------------------------
# 用户ID-课程ID-评分
userid_courseid_score_sql = """SELECT userid, courseid, projectid, (1+(browse_time/600)*4) AS score
                                    FROM (
                                    SELECT userid, courseid, projectid, IF(ISNULL(browse_time), 0, IF(browse_time/browse_count>600,600,browse_time/browse_count)) AS browse_time
                                    FROM {user_course_info}) as t"""\
    .format(user_course_info=USER_COURSE_INFO_TABLE)

# 用户ID-课程列表
userid_courselist = """SELECT {user_info}.userid AS userid, {user_info}.projectid AS projectid, course_list
                        FROM {user_info} JOIN (
                            SELECT projectid, activiesid, GROUP_CONCAT(courseid SEPARATOR '-') AS course_list
                            FROM {project_activies_course}
                            GROUP BY projectid, activiesid
                        ) AS t1 ON {user_info}.projectid = t1.projectid AND {user_info}.activiesid = t1.activiesid"""\
    .format(user_info=USER_INFO_TABLE, project_activies_course=PROJECT_ACTIVISE_COURSE)

# 用户信息
user_info = """SELECT userid, projectid, age, gender, schoolstagecode, subjectcode FROM {user_info}"""\
    .format(user_info=USER_INFO_TABLE)
