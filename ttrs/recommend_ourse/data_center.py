import pandas as pd
from ..utils import db_data
from ..settings import rs_course_setting as rs_set
import datetime
from collections import defaultdict
from ..settings.rs_course_setting import *


class CourseDataManager:
    def __init__(self):
        self.__user_course_score = None
        self.__user_info = None
        self.__user_course_list = None
        self.__user_projectid_list = None
        return

    # 加载(用户ID-课程ID-评分)数据
    def load_user_course_score(self):
        if not self.__user_course_score:
            # self.__user_course_score = pd.read_csv("./data/user_score_test2.csv", header=0)
            self.__user_course_score = db_data.read_db_to_df(sql=rs_set.userid_courseid_score_sql,
                                                             contain=['userid', 'courseid', 'projectid', 'score'],
                                                             info=rs_set.USER_COURSE_INFO_TABLE,
                                                             verbose=rs_set.VERBOSE)
            # 类型转换
            self.__user_course_score[['score']] = self.__user_course_score[["score"]].astype(float)

    # 加载(用户ID-选修课列表)数据
    def load_user_course_list(self):
        if not self.__user_course_list:
            # 需要设置mysql SET GLOBAL group_concat_max_len=1024*128;
            # tmp_data = pd.read_csv("./data/user_course_list.csv", header=0)
            tmp_data = db_data.read_db_to_df(sql=rs_set.userid_courselist,
                                             contain=['userid', 'projectid', 'course_list'],
                                             info=rs_set.USER_INFO_TABLE+' '+rs_set.PROJECT_ACTIVISE_COURSE,
                                             verbose=rs_set.VERBOSE)
            self.__user_course_list = []
            for uid, projectid, course_list in tmp_data.itertuples(index=False):
                self.__user_course_list.append((uid, projectid, set([int(iid) for iid in course_list.split('-')])))

    # 加载(用户信息)数据，处理成(用户ID-用户类型)
    def load_user_info(self):
        if self.__user_info is None:
            # data = pd.read_csv("./data/user_info.csv", header=0)
            contain_name = ['userid', 'projectid', 'age', 'gender', 'schoolstagecode', 'subjectcode']
            data = db_data.read_db_to_df(sql=rs_set.user_info, contain=contain_name,
                                         info=rs_set.USER_INFO_TABLE, verbose=rs_set.VERBOSE)
            data = data.fillna({'schoolstagecode': 'NULL', 'subjectcode': 'NULL', 'age': 0, 'gender': 1})
            self.__user_info = {}
            self.__user_projectid_list = defaultdict(set)
            for uid, projectid, age, gender, schoolstagecode,  subjectcodein in data[contain_name].itertuples(index=False):
                # 处理学科学段
                tmp_class = (schoolstagecode+'*'+subjectcodein).upper()
                # 处理年龄
                if age < 26:
                    tmp_class += '-0026'
                elif 26 <= age <= 30:
                    tmp_class += '-2630'
                elif 31 <= age <= 40:
                    tmp_class += '-3040'
                elif 41 <= age <= 50:
                    tmp_class += '-4150'
                else:
                    tmp_class += '-5000'
                # 处理性别：
                if gender == 2:
                    tmp_class += '-female'
                else:
                    tmp_class += '-male'
                self.__user_info[uid] = tmp_class
                self.__user_projectid_list[uid].add(projectid)

    def get_user_course_score(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        return self.__user_course_score[['userid', 'courseid', 'score']]

    def get_user_info(self):
        if self.__user_info is None:
            self.load_user_info()
        return self.__user_info

    # 构造普通用户选修课的预测数据，形如(用户ID-课程列表)
    def get_elective_course_pre_data(self):
        if self.__user_course_list is None:
            self.load_user_course_list()
        if self.__user_course_score is None:
            self.load_user_course_score()
        # 根据用户有过选课及浏览记录的课程构造过滤表
        filter_list = self.make_course_filter()
        # 选取在(用户ID-项目ID-选修课列表)和(用户ID-课程ID-评分)中同时出现的用户ID
        uid_list = set(self.__user_course_score['userid'].values)
        elective_course_pre_data = []
        for uid, projectid, course_list in self.__user_course_list:
            if uid in uid_list:
                elective_course_pre_data.append((uid, projectid, course_list-filter_list[uid]))
        return elective_course_pre_data

    # 构造冷启动用户选修课的预测数据，形如(用户ID-课程列表)
    def get_cold_elective_course_pre_data(self):
        if self.__user_course_list is None:
            self.load_user_course_list()
        if self.__user_course_score is None:
            self.load_user_course_score()
        # 选取在(用户ID-项目ID-选修课列表)中出现 但在(用户ID-课程ID-评分)中未出现的用户
        uid_list = set(self.__user_course_score['userid'].values)
        cold_elective_course_pre_data = []
        for uid, projectid, course_list in self.__user_course_list:
            if uid not in uid_list:
                cold_elective_course_pre_data.append((uid, projectid, course_list))
        return cold_elective_course_pre_data

    # 构造普通用户开放课程的预测数据，形如(用户ID-项目ID-课程列表)
    def get_open_course_pre_data(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        if self.__user_info is None:
            self.load_user_info()
        # 构造选课包
        pid_class_course_list = self.make_pid_class_course_list()
        # 根据用户有过选课及浏览记录的课程构造过滤表
        filter_list = self.make_course_filter()
        # 构造用户选课集, 选取在(用户ID-用户类型)和(用户ID-课程ID-评分)中同时出现的用户ID
        open_course_pre_data = []
        for uid in set(self.__user_course_score['userid'].values):
            if uid in self.__user_info:
                for projectid in self.__user_projectid_list[uid]:
                    user_msg = str(projectid) + '*' + self.__user_info[uid].split('-')[0]
                    candidate_list = pid_class_course_list[user_msg]
                    candidate_list = list(candidate_list - filter_list[uid])
                    if len(candidate_list) > 0:
                        open_course_pre_data.append((uid, projectid, candidate_list))
        return open_course_pre_data

    # 构造冷启动用户开放课程预测数据，形如(用户ID-项目ID-课程列表)
    def get_cold_open_course_pre_data(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        if self.__user_info is None:
            self.load_user_info()
        pid_class_course_list = self.make_pid_class_course_list()
        # 选取在(用户ID-用户类型)中出现 但在(用户ID-课程ID-评分)中未出现的用户
        cold_open_course_pre_data = []
        uid_list = set(self.__user_course_score['userid'].values)
        for uid, class_name in self.__user_info.items():
            if uid not in uid_list:
                for projectid in self.__user_projectid_list[uid]:
                    user_msg = str(projectid) + '*' + self.__user_info[uid].split('-')[0]
                    candidate_list = pid_class_course_list[user_msg]
                    if len(candidate_list) > 0:
                        cold_open_course_pre_data.append((uid, projectid, class_name, candidate_list))
        return cold_open_course_pre_data

    # 推荐结果保存到数据库
    def save_to_db(self, data, data_type):
        if self.__user_info is None:
            self.load_user_info()
        if data_type == 'elective_course_data':
            table_name = rs_set.COURSE_TABLE
            alldata_table_name = rs_set.ALLDATA_COURSE_TABLE
            stay_table_name = rs_set.STAY_COURSE_TABLE
        elif data_type == 'open_course_data':
            table_name = rs_set.OPEN_COURSE_TABLE
            alldata_table_name = rs_set.ALLDATA_OPEN_COURSE_TABLE
            stay_table_name = rs_set.STAY_OPEN_COURSE_TABLE
        else:
            return
        time = datetime.datetime.now().strftime('%Y-%m-%d')
        save_data = []
        uid_list = set()
        for uid, projectid, course_socre_list in data:
            if len(course_socre_list) > 0:
                uid_list.add(uid)
                tmp_ssc_sc = self.__user_info[uid].split('-')[0].split('*')
                ssc = tmp_ssc_sc[0]
                sc = tmp_ssc_sc[1]
                max_score = max(course_socre_list, key=lambda k: k[1])[1]
                min_score = min(course_socre_list, key=lambda k: k[1])[1]
                for courseid, score in course_socre_list:
                    save_data.append((uid, courseid, sc, ssc, projectid, time,
                                      round((rs_set.MAX_SCORE-rs_set.MIN_SCORE)*(score-min_score)/(max_score - min_score+1e-10)+rs_set.MIN_SCORE)))
        # 将数据保存到当周推荐数据表
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name=table_name, is_truncate=True)
        # 将数据保存到已完成项目推荐数据表
        db_data.delete_data_with_userid(list(uid_list), stay_table_name)
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name=stay_table_name, is_truncate=False)
        # 将数据保存到历史推荐数据表
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name=alldata_table_name, is_truncate=False)
        return

    # 根据用户有过选课及浏览记录的课程构造过滤表
    def make_course_filter(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        filter_list = {}
        for uid, iid, _, _ in self.__user_course_score.itertuples(index=False):
            if uid in filter_list:
                filter_list[uid].add(iid)
            else:
                filter_list[uid] = {iid}
        return filter_list

    # 构造开放课用户选课包
    def make_pid_class_course_list(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        if self.__user_info is None:
            self.load_user_info()
        pid_class_course_list = defaultdict(set)
        for uid, iid, projectid in self.__user_course_score[['userid', 'courseid', 'projectid']].itertuples(
                index=False):
            if uid in self.__user_info:
                user_msg = str(projectid) + '*' + self.__user_info[uid].split('-')[0]
                pid_class_course_list[user_msg].add(iid)
        return pid_class_course_list

