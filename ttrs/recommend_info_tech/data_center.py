from ..utils import db_data
from collections import defaultdict
import pandas as pd
from ..settings import rs_info_tech_setting as rs_set
from datetime import datetime, timedelta
import random


class InfoTechDataManager:
    def __init__(self):
        self.__user_item_data = None
        self.__user_info = None
        self.__user_projectid_list = None
        self.__new_item_list = None
        return

    def load_user_item_data(self):
        if self.__user_item_data is None:
            self.__user_item_data = db_data.read_db_to_df(sql=rs_set.user_item_data_sql,
                                                          contain=['userid', 'itemid'],
                                                          info=rs_set.USER_ITEM_BD_TABLE,
                                                          verbose=rs_set.VERBOSE)
        return

    def load_new_item_list(self):
        if self.__new_item_list is None:
            tmp_iid = db_data.read_db_to_df(sql=rs_set.new_item_id_sql,
                                            contain=['itemid'],
                                            info=rs_set.USER_ITEM_BD_TABLE,
                                            verbose=rs_set.VERBOSE)
            self.__new_item_list = set(tmp_iid['itemid'].values)
        return

    # 加载(用户信息)数据，处理成(用户ID-用户类型)
    def load_user_info(self):
        if self.__user_info is None:
            # data = pd.read_csv("./data/user_info.csv", header=0)
            contain_name = ['userid', 'projectid', 'age', 'gender', 'schoolstagecode', 'subjectcode']
            data = db_data.read_db_to_df(sql=rs_set.user_info_sql, contain=contain_name,
                                         info=rs_set.USER_INFO_TABLE, verbose=rs_set.VERBOSE)
            data = data.fillna({'schoolstagecode': 'NULL', 'subjectcode': 'NULL', 'age': 0, 'gender': 1})
            self.__user_info = {}
            self.__user_projectid_list = defaultdict(set)
            for uid, projectid, age, gender, schoolstagecode, subjectcodein in data[contain_name].itertuples(
                    index=False):
                # 处理学科学段
                tmp_class = (schoolstagecode + '*' + subjectcodein).upper()
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

    # 获取下周会关闭的项目id
    def get_close_project(self):
        close_project = db_data.read_db_to_df(sql=rs_set.project_id_close_sql,
                                              contain=['projectid', 'close_date'],
                                              info=rs_set.USER_INFO_TABLE, verbose=rs_set.VERBOSE)
        now = datetime.now()
        result = set()
        for pid, date in close_project.itertuples(index=False):
            if now + timedelta(days=7) > date.to_pydatetime():
                result.add(pid)
        return result

    def get_user_item_data(self):
        if self.__user_item_data is None:
            self.load_user_item_data()
        return self.__user_item_data

    def get_item_msg_data(self):
        result = db_data.read_db_to_df(sql=rs_set.item_msg_sql,
                                       contain=['itemid', 'content'],
                                       info=rs_set.INFO_TECH_MSG_TABLE,
                                       verbose=rs_set.VERBOSE)
        return result

    def get_item_score(self):
        item_score = db_data.read_db_to_df(sql=rs_set.item_score_sql,
                                           contain=['itemid', 'socre'],
                                           info=rs_set.INFO_TECH_MSG_TABLE,
                                           verbose=rs_set.VERBOSE)
        result = defaultdict(lambda: 20.0)
        for iid, score in item_score.itertuples(index=False):
            result[iid] = score
        return result

    def get_user_info(self):
        if self.__user_info is None:
            self.load_user_info()
        return self.__user_info

    def get_new_item_list(self):
        if self.__new_item_list is None:
            self.load_new_item_list()
        return self.__new_item_list

    # 构造用户信息技术技巧大全推荐集合
    # 选取在(用户ID-用户类型)和(用户ID-物品ID)中同时出现的用户
    def get_pre_data(self):
        if self.__user_info is None:
            self.load_user_info()
        if self.__user_item_data is None:
            self.load_user_item_data()
        if self.__new_item_list is None:
            self.load_new_item_list()
        # 构造信息技术技巧大全推荐集合
        item_list = set(self.__user_item_data['itemid'].values)
        # 根据用户有过选课及浏览记录的课程构造过滤表
        filter_list = self.make_item_filter()
        pre_data = []
        for uid in set(self.__user_item_data['userid'].values):
            if uid in self.__user_info:
                candidate_list = list(item_list - filter_list[uid] - self.__new_item_list)
                new_item_list = list(self.__new_item_list - filter_list[uid])
                if len(candidate_list) > 0:
                    pre_data.append((uid, candidate_list, new_item_list))
        return pre_data

    # 构造冷启动用户信息技术技巧大全推荐集合
    # 选取在(用户ID-用户类型)出现但在(用户ID-物品ID)没有出现的用户
    def get_cold_pre_data(self):
        if self.__user_info is None:
            self.load_user_info()
        if self.__user_item_data is None:
            self.load_user_item_data()
        if self.__new_item_list is None:
            self.load_new_item_list()
        tmp_user_id = set(self.__user_item_data['userid'].values)
        cold_pre_data = []
        recomend_new_num = min(len(self.__new_item_list), rs_set.RECOMMEND_NEW_NUM)
        for uid, info in self.__user_info.items():
            if uid not in tmp_user_id:
                # 构造(用户ID，用户类型， 随机抽样的新物品)
                cold_pre_data.append((uid, info, random.sample(self.__new_item_list, recomend_new_num)))
        return cold_pre_data

    # 构造冷启动模型训练数据
    def get_cold_train_data(self):
        if self.__user_item_data is None:
            self.load_user_item_data()
        if self.__new_item_list is None:
            self.load_new_item_list()
        result = []
        for uid, iid in self.__user_item_data[['userid', 'itemid']].itertuples(index=False):
            if iid not in self.__new_item_list:
                result.append((uid, iid))
        result = pd.DataFrame(result, columns=['userid', 'itemid'])
        return result

    def save_to_db(self, data):
        if self.__user_info is None:
            self.load_user_info()
        time = db_data.get_time_from_db(table_name=rs_set.USER_INFO_TABLE, colum_name='dt', verbose=rs_set.VERBOSE)
        close_project = self.get_close_project()
        save_data = []
        stay_data = []
        pid_list = set()
        for uid, item_list in data:
            if len(item_list) > 0:
                tmp_ssc_sc = self.__user_info[uid].split('-')[0].split('*')
                ssc = tmp_ssc_sc[0]
                sc = tmp_ssc_sc[1]
                item_num = len(item_list)
                for i in range(item_num-1, -1, -1):
                    iid = item_list[i][0]
                    score = round(i * (rs_set.MAX_SCORE - rs_set.MIN_SCORE) / (item_num - 1 + 1e-4) + rs_set.MIN_SCORE, 4)
                    for projectid in self.__user_projectid_list[uid]:
                        pid_list.add(projectid)
                        save_data.append((uid, iid, sc, ssc, projectid, time, score))
                        if projectid in close_project:
                            stay_data.append((uid, iid, sc, ssc, projectid, time, score))
        # 将数据保存到当周推荐数据表
        if len(save_data) > 0:
            db_data.save_data_to_db(save_data,
                                    contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                             'recommendation_index'],
                                    table_name=rs_set.RESULT_TABLE, is_truncate=True, verbose=rs_set.VERBOSE)
        # 将数据保存到历史推荐数据表
        if len(save_data) > 0:
            db_data.save_data_to_db(save_data,
                                    contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                             'recommendation_index'],
                                    table_name=rs_set.ALLDATA_TABLE, is_truncate=False, verbose=rs_set.VERBOSE)
        del save_data
        # 将数据保存到已完成项目推荐数据表
        if len(stay_data) > 0:
            db_data.delete_data_with_projectid(list(pid_list), rs_set.STAY_TABLE, verbose=rs_set.VERBOSE)
            db_data.save_data_to_db(stay_data,
                                    contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                             'recommendation_index'],
                                    table_name=rs_set.STAY_TABLE, is_truncate=False, verbose=rs_set.VERBOSE)
        return

    def make_item_filter(self):
        if self.__user_item_data is None:
            self.load_user_item_data()
        filter_list = defaultdict(set)
        for uid, iid, in self.__user_item_data.itertuples(index=False):
            filter_list[uid].add(iid)
        return filter_list



