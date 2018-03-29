from ..utils import db_data
from collections import defaultdict


class NoteShareDataManager:
    def __init__(self):
        self.user_info = None
        self.user_projectid_list = None
        self.user_item = None
        self.pid_item_list = None
        return

    def load_user_info(self):
        if self.user_info is None:
            contain_name = ['userid', 'projectid', 'schoolstagecode', 'subjectcode']
            data = db_data.read_db_to_df(sql="", contain=contain_name,
                                         info="", verbose=True)
            data = data.fillna({'schoolstagecode': 'NULL', 'subjectcode': 'NULL', 'age': 0, 'gender': 1})
            self.user_info = {}
            self.user_projectid_list = defaultdict(set)
            for uid, projectid, schoolstagecode, subjectcodein in data[contain_name].itertuples(index=False):
                # 处理学科学段
                tmp_class = (schoolstagecode + '-' + subjectcodein).upper()
                self.user_info[uid] = tmp_class
                self.user_projectid_list[uid].add(projectid)
        return

    def load_user_item(self):
        if self.user_item is None:
            self.user_item = db_data.read_db_to_df(sql="", contain=['userid', 'projectid', 'itemid'],
                                                   info="", verbose=True)
        return

    def load_content_train_data(self):
        result = db_data.read_db_to_df(sql="",
                                       contain=['itemid', 'projectid', 'content'],
                                       info="",
                                       verbose=True)
        if self.pid_item_list is None:
            self.pid_item_list = defaultdict(set)
            for iid, pid, _ in result.itertuples(index=False):
                self.pid_item_list[pid].add(iid)
        return result

    def get_item_score(self):
        data = db_data.read_db_to_df(sql="",
                                     contain=['itemid', 'score'],
                                     info="",
                                     verbose=True)
        item_score = defaultdict(float)
        for iid, score in data.itertuples(index=False):
            item_score[iid] = score
        return item_score

    # 选取在用户信息表和（用户-物品）表都出现的用户
    def get_pre_data(self):
        if self.user_info is None:
            self.load_user_info()
        if self.user_item is None:
            self.load_user_item()
        if self.pid_item_list is None:
            self.load_content_train_data()
        # 获取用户最近浏览的物品
        user_near_item = self.get_user_near_item()
        # 构造用户选课集, 选取在(用户ID-用户类型)和(用户ID-课程ID-评分)中同时出现的用户ID
        pre_data = []
        for uid in set(self.user_item['userid'].values):
            if uid in self.user_info:
                for pid in self.user_projectid_list[uid]:
                    candidate_list = self.pid_item_list[pid]
                    near_item = user_near_item[str(uid)+'-'+str(pid)]
                    candidate_list = list(candidate_list - near_item)
                    pre_num = 10//len(near_item)
                    if len(candidate_list) > 0:
                        pre_data.append((uid, pid, near_item, pre_num, candidate_list))
        return pre_data

    # 选取在用户信息表出现但在（用户-物品）表未出现的用户
    def get_cold_pre_data(self):
        if self.user_info is None:
            self.load_user_info()
        if self.user_item is None:
            self.load_user_item()
        if self.pid_item_list is None:
            self.load_content_train_data()
        uid_set = set(self.user_item['userid'].values)
        cold_pre_data = []
        for uid, pid_list in self.user_projectid_list.items():
            if uid in uid_set:
                for pid in pid_list:
                    candidate_list = self.pid_item_list[pid]
                    cold_pre_data.append((uid, pid, candidate_list))
        return cold_pre_data

    def save_to_db(self, data):
        if self.user_info is None:
            self.load_user_info()
        time = db_data.get_time_from_db(table_name="", colum_name='dt')
        save_data = []
        uid_list = set()
        for uid, pid, item_list in data:
            if len(item_list) > 0:
                uid_list.add(uid)
                tmp_ssc_sc = self.user_info[uid].split('-')
                ssc = tmp_ssc_sc[0]
                sc = tmp_ssc_sc[1]
                item_num = len(item_list)
                for i in range(item_num, 0, -1):
                    iid = item_list[i-1]
                    score = i*(100-80)/item_num+80
                    save_data.append((uid, iid, sc, ssc, pid, time, score))
        # 将数据保存到当周推荐数据表
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name="", is_truncate=True, verbose=True)
        # 将数据保存到已完成项目推荐数据表
        db_data.delete_data_with_userid(list(uid_list), "")
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name="", is_truncate=False, verbose=True)
        # 将数据保存到历史推荐数据表
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name="", is_truncate=False, verbose=True)
        return

    def get_user_near_item(self):
        if self.user_item is None:
            self.load_user_item()
        user_near_item = defaultdict(set)
        for uid, pid, iid in self.user_item.itertuples(index=False):
            user_near_item[str(uid)+'-'+str(pid)].add(iid)
        return user_near_item
