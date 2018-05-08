from ..utils import db_data
from collections import defaultdict
from ..settings import rs_note_share_setting as rs_set
from datetime import datetime, timedelta


class NoteShareDataManager:
    def __init__(self):
        self.user_info = None
        self.user_projectid_list = None
        self.user_item = None
        self.pid_item_list = None
        self.item_projectid_score = None
        return

    def load_user_info(self):
        if self.user_info is None:
            contain_name = ['userid', 'projectid', 'schoolstagecode', 'subjectcode']
            data = db_data.read_db_to_df(sql=rs_set.user_info_sql, contain=contain_name,
                                         info=rs_set.USER_INFO_TABLE, verbose=rs_set.VERBOSE)
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
            self.user_item = db_data.read_db_to_df(sql=rs_set.user_item_sql, contain=['userid', 'projectid', 'itemid'],
                                                   info=rs_set.USER_ITEM_TABLE, verbose=rs_set.VERBOSE)
        return

    def load_user_near_item(self):
        data = db_data.read_db_to_df(sql=rs_set.user_near_item_sql, contain=['userid', 'projectid', 'itemid'],
                                     info=rs_set.USER_ITEM_TABLE, verbose=rs_set.VERBOSE)
        return data

    def load_content_train_data(self):
        result = db_data.read_db_to_df(sql=rs_set.item_content_sql, contain=['itemid', 'projectid', 'content'],
                                       info=rs_set.ITEM_MSG_TABEL, verbose=rs_set.VERBOSE)
        if self.pid_item_list is None:
            self.pid_item_list = defaultdict(set)
            for iid, pid, _ in result.itertuples(index=False):
                self.pid_item_list[pid].add(iid)
        return result

    def load_item_projectid_score(self):
        if self.item_projectid_score is None:
            self.item_projectid_score = db_data.read_db_to_df(sql=rs_set.item_score_sql, contain=['itemid', 'projectid', 'score'],
                                                              info=rs_set.ITEM_MSG_TABEL, verbose=rs_set.VERBOSE)
        return

    def get_user_item(self):
        if self.user_item is None:
            self.load_user_item()
        return self.user_item

    def get_item_score(self):
        if self.item_projectid_score is None:
            self.load_item_projectid_score()
        item_score = defaultdict(float)
        for iid, _, score in self.item_projectid_score.itertuples(index=False):
            item_score[iid] = score
        return item_score

    def get_item_projectid_score(self):
        if self.item_projectid_score is None:
            self.load_item_projectid_score()
        return self.item_projectid_score

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
                    candidate_list = candidate_list - near_item
                    if len(near_item) > 0:
                        pre_num = max(rs_set.CONTENT_RECOMMEND_NUM//len(near_item), 1)
                    else:
                        pre_num = 0
                    if len(candidate_list) > 0:
                        pre_data.append((uid, pid, near_item, pre_num, candidate_list))
        return pre_data

    # 选取在用户信息表出现但在（用户-物品）表未出现的用户
    def get_cold_pre_data(self):
        if self.user_info is None:
            self.load_user_info()
        if self.user_item is None:
            self.load_user_item()
        uid_set = set(self.user_item['userid'].values)
        cold_pre_data = []
        for uid, pid_list in self.user_projectid_list.items():
            if uid not in uid_set:
                for pid in pid_list:
                    cold_pre_data.append((uid, pid))
        return cold_pre_data

    def save_to_db(self, data):
        if self.user_info is None:
            self.load_user_info()
        time = db_data.get_time_from_db(table_name=rs_set.USER_INFO_TABLE, colum_name='dt', verbose=rs_set.VERBOSE)
        close_project = self.get_close_project()
        save_data = []
        stay_data = []
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
                    if pid in close_project:
                        stay_data.append((uid, iid, sc, ssc, pid, time, score))
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
        # 将数据保存到已完成项目推荐数据表
        if len(stay_data) > 0:
            db_data.save_data_to_db(stay_data,
                                    contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                             'recommendation_index'],
                                    table_name=rs_set.STAY_TABLE, is_truncate=False, verbose=rs_set.VERBOSE)
        return

    def get_user_near_item(self):
        user_item = self.load_user_near_item()
        user_near_item = defaultdict(set)
        for uid, pid, iid in user_item.itertuples(index=False):
            user_near_item[str(uid)+'-'+str(pid)].add(iid)
        return user_near_item
