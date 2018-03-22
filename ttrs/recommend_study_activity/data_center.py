from ..utils import db_data
from collections import defaultdict
from ..settings import rs_study_activity_setting as rs_set
import random
import datetime


class StudyActivityDataManager:
    def __init__(self):
        self.user_activity_data = None
        return

    # 加载用户-活动参与信息
    def load_user_activity_data(self):
        if self.user_activity_data is None:
            self.user_activity_data = db_data.read_db_to_df(sql="",
                                                            contain=['userid', 'schoolstagecode', 'subjectcode', 'itemid'],
                                                            info="",
                                                            verbose=True)
        return

    # 获取用户-活动参与信息
    def get_user_activity_data(self):
        if self.user_activity_data is None:
            self.load_user_activity_data()
        return self.user_activity_data

    # 获取用户信息表
    def get_user_info(self):
        result = db_data.read_db_to_df(sql="",
                                       contain=['userid', 'projectid', 'schoolstagecode', 'subjectcode'],
                                       info="",
                                       verbose=True)
        return result

    # 获取候选推荐列表
    def get_candidate_list(self):
        activity_info = db_data.read_db_to_df(sql="",
                                              contain=['itemid', 'projectid', 'schoolstagecode', 'subjectcode'],
                                              info="",
                                              verbose=True)
        candidate_list = defaultdict(set)
        for iid, pid, ssc, sc in activity_info.itertuples(index=False):
            candidate_list[str(pid)+'-'+ssc+'-'+sc].add(iid)
        return candidate_list

    # 获取新活动列表
    def get_new_item_list(self):
        activity_info = db_data.read_db_to_df(sql="",
                                              contain=['itemid', 'projectid', 'schoolstagecode', 'subjectcode'],
                                              info="",
                                              verbose=True)
        new_item_list = defaultdict(set)
        for iid, pid, ssc, sc in activity_info.itertuples(index=False):
            new_item_list[str(pid) + '-' + ssc + '-' + sc].add(iid)
        return new_item_list

    # 获取预测数据
    def get_pre_data(self):
        # 获取用户信息，过滤表，候选推荐表，新物品表
        user_info = self.get_user_info()
        filter_list = self.get_filter_list()
        cnadidate_list = self.get_candidate_list()
        new_item_list = self.get_new_item_list()

        pre_data = []
        for uid, pid, ssc, sc in user_info.itertuples(index=False):
            tmp_key = str(pid) + '-' + ssc + '-' + sc
            if tmp_key in cnadidate_list:
                item_list = list(cnadidate_list[tmp_key] - filter_list[uid])
                new_list = list(new_item_list[tmp_key] - filter_list[uid])
                new_list = random.sample(new_list, min(len(new_list), 3))
                pre_data.append((uid, pid, ssc, sc, item_list, new_list))
        return pre_data

    def save_to_db(self, data):
        table_name = ""
        alldata_table_name = ""
        stay_table_name = ""

        time = datetime.datetime.now().strftime('%Y-%m-%d')
        save_data = []
        uid_list = set()
        for uid, pid, ssc, sc, item_list in data:
            if len(item_list) > 0:
                uid_list.add(uid)
                item_num = len(item_list)
                for i in range(item_num-1, -1, -1):
                    iid = item_list[i]
                    score = i*(rs_set.MAX_SCORE-rs_set.MIN_SCORE)/(item_num-1)+rs_set.MIN_SCORE
                    save_data.append((uid, iid, sc, ssc, pid, time, score))
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

    # 获取用户已参与过的活动，构造过滤表
    def get_filter_list(self):
        if self.user_activity_data is None:
            self.load_user_activity_data()
        filter_list = defaultdict(set)
        for uid, _, _, iid in self.user_activity_data.itertuples(index=False):
            filter_list[uid].add(iid)
        return filter_list
