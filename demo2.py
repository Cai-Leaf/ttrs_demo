from ttrs.data_connect.db_data import *
import pandas as pd
from ttrs.course_recommender_system.data_center import *

# userid_courselist = """SELECT user_info.userid AS userid, course_list
#                         FROM user_info JOIN (
#                             SELECT projectid, activiesid, GROUP_CONCAT(courseid SEPARATOR '-') AS course_list
#                             FROM project_activies_course
#                             GROUP BY projectid, activiesid
#                         ) AS t1 ON user_info.projectid = t1.projectid AND user_info.activiesid = t1.activiesid"""
# data = read_db_to_df(sql=userid_courselist, contain=['userid', 'courselist'])
# test = []
# for uid, course_list in data.itertuples(index=False):
#     test.append((uid, [int(iid) for iid in course_list.split('-')]))
# print(sum([len(item[1]) for item in test]))
    # save_big_data_to_db_multiprocessing(data, contain=['id', 'name', 'age'], table_name='id_name_age', is_truncate=True)
# aaa = [[i for i in item] for item in data.itertuples(index=False)]
# print(aaa)

data_manager = CourseDataManager()
data_manager.load_user_course_score()
data_manager.load_user_info()
data_manager.load_user_course_list()
