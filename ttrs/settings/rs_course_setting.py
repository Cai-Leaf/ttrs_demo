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
USER_COURSE_INFO_TABLE = 'user_course_info'

# 表6.项目—学习任务—选修课列表
PROJECT_ACTIVISE_COURSE = 'project_activies_course'


# SQL语句 ----------------------------------------------------
# 用户ID-课程ID-评分
userid_courseid_score_sql = """SELECT userid, courseid, (is_select+(browse_time/600)*4) AS score
                               FROM (
                                    SELECT t1.userid AS userid, t1.courseid AS courseid, IFNULL(is_select,1) AS is_select, IF(ISNULL(browse_time),0,IF(browse_time>600,600,browse_time)) AS browse_time
                                    FROM (
                                    (
                                        SELECT userid, courseid
                                        FROM user_cource_select
                                        WHERE courseid IN (
                                            SELECT courseid
                                            FROM course
                                        )
                                    )
                                    UNION
                                    (
                                        SELECT userid, courseid
                                        FROM user_course_browse
                                        WHERE courseid IN (
                                            SELECT courseid
                                            FROM course
                                        )
                                    )) AS t1
                                    LEFT JOIN (
                                        SELECT userid, courseid, @tmp:=1 AS is_select
                                        FROM user_cource_select
                            
                                    ) AS t2 ON t1.userid = t2.userid AND t1.courseid = t2.courseid
                                    LEFT JOIN (
                                        SELECT userid, courseid, browse_time/browse_count AS browse_time
                                        FROM user_course_browse
                            
                                    ) AS t3 ON t1.userid = t3.userid AND t1.courseid = t3.courseid) AS t"""

# 用户ID-课程列表
userid_courselist = """SELECT {user_info}.userid AS userid, course_list
                        FROM {user_info} JOIN (
                            SELECT projectid, activiesid, GROUP_CONCAT(courseid SEPARATOR '-') AS course_list
                            FROM {project_activies_course}
                            GROUP BY projectid, activiesid
                        ) AS t1 ON {user_info}.projectid = t1.projectid AND {user_info}.activiesid = t1.activiesid"""\
    .format(user_info=USER_INFO_TABLE, project_activies_course=PROJECT_ACTIVISE_COURSE)

# 用户信息
user_info = """SELECT userid, projectid, age, gender, schoolstagecode, subjectcode FROM {user_info}"""\
    .format(user_info=USER_INFO_TABLE)
