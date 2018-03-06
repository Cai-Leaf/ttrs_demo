"""
选修课推荐系统
开放课程推荐系统
配置文件
"""
# 模型相关 ----------------------------------------------------
# 推荐课程数
RECOMMEND_COURSE_NUM = 20

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
userid_courselist = """SELECT user_info.userid AS userid, course_list
                        FROM user_info JOIN (
                            SELECT projectid, activiesid, GROUP_CONCAT(courseid SEPARATOR '-') AS course_list
                            FROM project_activies_course
                            GROUP BY projectid, activiesid
                        ) AS t1 ON user_info.projectid = t1.projectid AND user_info.activiesid = t1.activiesid"""

# 用户信息
user_info = """SELECT userid, age, gender, schoolstagecode
               FROM user_info"""

