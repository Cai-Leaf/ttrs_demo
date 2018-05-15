"""
选修课推荐系统
开放课程推荐系统
配置文件
"""
# 基本设置 ----------------------------------------------------
# 是否输出运行信息
VERBOSE = True

# 选修课推荐课程数
RECOMMEND_COURSE_NUM = 5

# 开放课推荐课程数
RECOMMEND_OPEN_COURSE_NUM = 5

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
# 项目-用户信息表
USER_INFO_TABLE = 'ts501'

# 课程—用户行为
USER_COURSE_INFO_TABLE = 'ts502'

# 学习任务—选修课列表
PROJECT_ACTIVISE_COURSE = 'ts504'


# SQL语句 ----------------------------------------------------
# 用户ID-课程ID-评分
userid_courseid_score_sql = """SELECT userid, courseid, projectid, (1+(browse_time/600)*4) AS score
                               FROM (
                               SELECT userid, courseid, projectid, IF(pv=0, 0, IF(duration/pv>600,600,duration/pv)) AS browse_time
                               FROM (
                                    SELECT userid, courseid, projectid, SUM(pv) as pv, SUM(duration) as duration
                                    FROM {user_course_info}
                                    GROUP BY userid, courseid
                               ) as t ) as t1"""\
    .format(user_course_info=USER_COURSE_INFO_TABLE)

# 用户ID-课程列表
userid_courselist = """SELECT userid, projectid, activiesid, course_package_id, course_list
                       FROM {project_activies_course}"""\
    .format(project_activies_course=PROJECT_ACTIVISE_COURSE)

# 用户信息
user_info = """SELECT userid, projectid, age, gender, schoolstagecode, subjectcode FROM {user_info}"""\
    .format(user_info=USER_INFO_TABLE)

# 项目-关闭时间表
project_id_close_sql = "SELECT DISTINCT projectid, project_endtime FROM {user_info}".format(user_info=USER_INFO_TABLE)
