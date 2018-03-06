import pandas as pd
from ..data_connect import db_data
from ..settings import course_rs_setting as rs_set
import heapq


class CourseDataManager:
    def __init__(self):
        self.__user_course_score = None
        self.__user_info = None
        self.__user_course_list = None
        return

    # 加载(用户ID-课程ID-评分)数据
    def load_user_course_score(self):
        if not self.__user_course_score:
            # self.__user_course_score = pd.read_csv("./data/user_score_test2.csv", header=0)
            self.__user_course_score = db_data.read_db_to_df(sql=rs_set.userid_courseid_score_sql,
                                                             contain=['userid', 'courseid', 'score'])
            # 类型转换
            self.__user_course_score[['score']] = self.__user_course_score[["score"]].astype(float)

    # 加载(用户ID-选修课列表)数据
    def load_user_course_list(self):
        if not self.__user_course_list:
            # 需要设置mysql SET GLOBAL group_concat_max_len=1024*128;
            # tmp_data = pd.read_csv("./data/user_course_list.csv", header=0)
            tmp_data = db_data.read_db_to_df(sql=rs_set.userid_courselist,
                                             contain=['userid', 'course_list'])
            self.__user_course_list = []
            for uid, course_list in tmp_data.itertuples(index=False):
                self.__user_course_list.append((uid, [int(iid) for iid in course_list.split('-')]))

    # 加载(用户信息)数据，处理成(用户ID-用户类型)
    def load_user_info(self):
        if self.__user_info is None:
            # data = pd.read_csv("./data/user_info.csv", header=0)
            data = db_data.read_db_to_df(sql=rs_set.user_info,
                                         contain=['userid', 'age', 'gender', 'schoolstagecode'])
            data = data.fillna({'schoolstagecode': 'NULL', 'age': 0, 'gender': 3})
            self.__user_info = {}
            for uid, age, gender, sc_code in data[['userid', 'age', 'gender', 'schoolstagecode']].itertuples(index=False):
                tmp_class = 'class'
                # 处理学段
                if len(sc_code) >= 2 and sc_code[:2].upper() == 'YE':
                    tmp_class += '-YE'
                elif len(sc_code) >= 2 and sc_code[:2].upper() == 'XX':
                    tmp_class += '-XX'
                elif len(sc_code) >= 2 and sc_code[:2].upper() in {'CZ', 'ZX', 'YJ'}:
                    tmp_class += '-CZ'
                elif len(sc_code) >= 2 and sc_code[:2].upper() == 'GZ':
                    tmp_class += '-GZ'
                elif len(sc_code) >= 2 and sc_code[:2].upper() == 'ZZ':
                    tmp_class += '-ZZ'
                else:
                    self.__user_info[uid] = "class-other"
                    continue
                # 处理年龄
                if age < 26:
                    tmp_class += '-26'
                elif 26 <= age <= 30:
                    tmp_class += '-2630'
                elif 31 <= age <= 40:
                    tmp_class += '-3040'
                elif 41 <= age <= 50:
                    tmp_class += '-4150'
                else:
                    tmp_class += '-50'
                # 处理性别：
                if gender == 2:
                    tmp_class += '-female'
                else:
                    tmp_class += '-male'
                self.__user_info[uid] = tmp_class

    def get_user_course_score(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        return self.__user_course_score

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
        # 选取在(用户ID-选修课列表)和(用户ID-课程ID-评分)中同时出现的用户ID
        uid_list = set(self.__user_course_score['userid'].values)
        elective_course_pre_data = []
        for uid, course_list in self.__user_course_list:
            if uid in uid_list:
                elective_course_pre_data.append((uid, course_list))
        return elective_course_pre_data

    # 构造冷启动用户选修课的预测数据，形如(用户ID-课程列表)
    def get_cold_elective_course_pre_data(self):
        if self.__user_course_list is None:
            self.load_user_course_list()
        if self.__user_course_score is None:
            self.load_user_course_score()
        # 选取在(用户-选修课列表)中出现 但在(用户ID-课程ID-评分)中未出现的用户
        uid_list = set(self.__user_course_score['userid'].values)
        cold_elective_course_pre_data = []
        for uid, course_list in self.__user_course_list:
            if uid not in uid_list:
                cold_elective_course_pre_data.append((uid, course_list))
        return cold_elective_course_pre_data

    # 构造普通用户开放课程的预测数据，形如(用户ID-课程列表)
    def get_open_course_pre_data(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        if self.__user_info is None:
            self.load_user_info()
        # 统计各用户类别中出现的课程及其出现次数
        class_course = {"class-other": dict()}
        for uid, iid, r in self.__user_course_score.itertuples(index=False):
            if uid in self.__user_info:
                if self.__user_info[uid] in class_course:
                    if iid in class_course[self.__user_info[uid]]:
                        class_course[self.__user_info[uid]][iid] += 1
                    else:
                        class_course[self.__user_info[uid]][iid] = 1
                else:
                    class_course[self.__user_info[uid]] = {iid: 1}
            else:
                if iid in class_course["class-other"]:
                    class_course["class-other"][iid] += 1
                else:
                    class_course["class-other"][iid] = 1
        # 根据用户有过选课及浏览记录的课程构造过滤表
        filter_list = {}
        for uid, iid, _ in self.__user_course_score.itertuples(index=False):
            if uid in filter_list:
                filter_list[uid].add(iid)
            else:
                filter_list[uid] = {iid}
        # 根据各类别中课程出现的次数构造课程候选集
        candidate_list = {}
        for key, val in class_course.items():
            val = sorted(val.items(), key=lambda k: k[1], reverse=True)[:len(val) // 3]
            candidate_list[key] = set([v[0] for v in val])
        # 构造用户选课集
        open_course_pre_data = []
        for uid in set(self.__user_course_score['userid'].values):
            uid_class = self.__user_info.get(uid, "class-other")
            open_course_pre_data.append((uid, list(candidate_list[uid_class] - filter_list[uid])))
        return open_course_pre_data

    # 构造冷启动用户开放课程预测数据，形如(用户ID-用户类型)
    def get_cold_open_course_pre_data(self):
        if self.__user_course_score is None:
            self.load_user_course_score()
        if self.__user_info is None:
            self.load_user_info()
        # 选取在(用户ID-用户类型)中出现 但在(用户ID-课程ID-评分)中未出现的用户
        cold_open_course_pre_data = []
        uid_list = set(self.__user_course_score['userid'].values)
        for uid, class_name in self.__user_info.items():
            if uid not in uid_list:
                cold_open_course_pre_data.append((uid, class_name))
        return cold_open_course_pre_data

    def save_to_db(self, data, data_type):
        if data_type == 'elective_course_data':
            table_name = 'elective_course_result'
        elif data_type == 'open_course_data':
            table_name = 'open_course_result'
        else:
            return
        save_data = []
        for uid, course_socre_list in data:
            max_score = max(course_socre_list, key=lambda k: k[1])[1]
            min_score = min(course_socre_list, key=lambda k: k[1])[1]
            for courseid, score in course_socre_list:
                save_data.append((uid, courseid, round(40 * (score - min_score) / (max_score - min_score + 1e-10) + 60)))
        db_data.save_big_data_to_db(save_data, contain=['userid', 'courseid', 'score'], table_name=table_name, is_truncate=True)
        return
