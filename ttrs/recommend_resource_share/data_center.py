from ..utils import db_data
from collections import defaultdict
from ..settings import rs_resource_share_setting as rs_set


class ResourceShareDataManager:
    def __init__(self):
        self.user_item = None
        self.user_info = None
        self.user_projectid = None
        self.item_msg_data = None
        return

    def load_user_item(self):
        if self.user_item is None:
            self.user_item = db_data.read_db_to_df(sql=rs_set.user_item_sql,
                                                   contain=['userid', 'itemid', 'projectid'],
                                                   info=rs_set.USER_ITEM_TABLE, verbose=rs_set.VERBOSE)
        return

    def load_user_info(self):
        if self.user_info is None:
            contain_name = ['userid', 'projectid', 'age', 'gender', 'schoolstagecode', 'subjectcode']
            data = db_data.read_db_to_df(sql=rs_set.user_info_sql, contain=contain_name,
                                         info=rs_set.USER_INFO_TABLE, verbose=rs_set.VERBOSE)
            data = data.fillna({'schoolstagecode': 'NULL', 'subjectcode': 'NULL', 'age': 0, 'gender': 1})
            self.user_info = {}
            self.user_projectid = defaultdict(set)
            for uid, projectid, age, gender, schoolstagecode, subjectcodein in data[contain_name].itertuples(index=False):
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
                self.user_info[uid] = tmp_class
                self.user_projectid[uid].add(projectid)

    def load_item_msg_data(self):
        if self.item_msg_data is None:
            self.item_msg_data = db_data.read_db_to_df(sql=rs_set.item_score_sql,
                                                       contain=['itemid', 'projectid', 'classname', 'score'],
                                                       info=rs_set.ITEM_MSG_TABEL, verbose=rs_set.VERBOSE)
        return

    def get_user_near_browse(self):
        if self.user_item is None:
            self.load_user_item()
        user_near_browse = defaultdict(set)
        for uid, iid, pid in self.user_item.itertuples(index=False):
            user_near_browse[uid].add(iid)
        return user_near_browse

    def get_item_msg_data(self):
        if self.item_msg_data is None:
            self.load_item_msg_data()
        return self.item_msg_data

    def get_user_item(self):
        if self.user_item is None:
            self.load_user_item()
        return self.user_item

    def get_user_info(self):
        if self.user_info is None:
            self.load_user_info()
        return self.user_info

    def get_pre_data(self):
        if self.user_info is None:
            self.load_user_info()
        if self.user_item is None:
            self.load_user_item()
        # 候选物品列表
        pid_candidate_list = self.make_pid_candidate_list()
        # 过滤列表
        filter_list = self.make_filter_list()
        # 物品—类型
        item_class = self.make_item_class()
        # 用户-最近浏览物品
        user_nrea_browse = self.get_user_near_browse()

        # 选取在(用户ID-用户类型)和(用户ID-物品ID-项目ID)中同时出现的用户
        pre_data = []
        uid_list = set(self.user_item['userid'].values)
        for uid, info in self.user_info.items():
            if uid in uid_list:
                for projectid in self.user_projectid[uid]:
                    # 构造协同过滤算法使用的候选集
                    candidate_list = pid_candidate_list[projectid]
                    candidate_list = candidate_list - filter_list[uid]

                    # 构造类别算法使用的候选集
                    class_count = defaultdict(int)
                    all_count = 0
                    # 计算用户最近浏览的资源中，各类别的数量
                    for iid in user_nrea_browse[uid]:
                        class_count[item_class[iid]] += 1
                        all_count += 1
                    # 将候选集中的资源，按类别划分
                    tmp_class_iid_list = defaultdict(set)
                    for iid in candidate_list:
                        iid_class_name = item_class[iid]
                        if iid_class_name in class_count:
                            tmp_class_iid_list[iid_class_name].add(iid)
                    # 将划分后的类别-资源列表加入预测集
                    class_iid_list = []
                    for class_name, iid_list in tmp_class_iid_list.items():
                        num = int(rs_set.MODEL1_RECOMMEND_NUM * (class_count[class_name]/all_count))
                        class_iid_list.append((class_name, iid_list, num))

                    # 将数据加入预测数据集
                    pre_data.append((uid, projectid, candidate_list, class_iid_list))
        return pre_data

    # 构造冷启动用户预测数据
    def get_cold_pre_data(self):
        if self.user_item is None:
            self.load_user_item()
        if self.user_info is None:
            self.load_user_info()
        pid_candidate_list = self.make_pid_candidate_list()
        # 选取在(用户ID-用户类型)中出现 但在(用户ID-物品ID-项目ID)中未出现的用户
        pre_data = []
        uid_list = set(self.user_item['userid'].values)
        for uid, class_name in self.user_info.items():
            if uid not in uid_list:
                for projectid in self.user_projectid[uid]:
                    candidate_list = pid_candidate_list[projectid]
                    if len(candidate_list) > 0:
                        pre_data.append((uid, projectid, class_name, candidate_list))
        return pre_data

    def make_pid_candidate_list(self):
        if self.item_msg_data is None:
            self.load_item_msg_data()
        pid_candidate_list = defaultdict(set)
        for iid, pid, _, _ in self.item_msg_data[['itemid', 'projectid', 'classname', 'score']].itertuples(
                index=False):
            pid_candidate_list[pid].add(iid)
        return pid_candidate_list

    def make_filter_list(self):
        if self.user_item is None:
            self.load_user_item()
        filter_list = defaultdict(set)
        for uid, iid, _ in self.user_item.itertuples(index=False):
            filter_list[uid].add(iid)
        return filter_list

    def make_item_class(self):
        if self.item_msg_data is None:
            self.load_item_msg_data()
        item_class = defaultdict(lambda: 'default')
        for iid, pid, class_mame, _ in self.item_msg_data[['itemid', 'projectid', 'classname', 'score']].itertuples(index=False):
            item_class[iid] = class_mame
        return item_class

    def save_to_db(self, data):
        if self.user_info is None:
            self.load_user_info()
        time = db_data.get_time_from_db(table_name=rs_set.USER_ITEM_TABLE, colum_name='dt')
        save_data = []
        uid_list = set()
        for uid, pid, item_list in data:
            if len(item_list) > 0:
                uid_list.add(uid)
                tmp_ssc_sc = self.user_info[uid].split('-')[0].split('*')
                ssc = tmp_ssc_sc[0]
                sc = tmp_ssc_sc[1]
                item_num = len(item_list)
                for i in range(item_num, 0, -1):
                    iid = item_list[i-1]
                    score = i * (rs_set.MAX_SCORE - rs_set.MIN_SCORE) / item_num + rs_set.MIN_SCORE
                    save_data.append((uid, iid, sc, ssc, pid, time, score))
        # 将数据保存到当周推荐数据表
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name=rs_set.RESULT_TABLE, is_truncate=True, verbose=rs_set.VERBOSE)
        # 将数据保存到已完成项目推荐数据表
        db_data.delete_data_with_userid(list(uid_list), rs_set.STAY_TABLE, verbose=rs_set.VERBOSE)
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name=rs_set.STAY_TABLE, is_truncate=False, verbose=rs_set.VERBOSE)
        # 将数据保存到历史推荐数据表
        db_data.save_data_to_db(save_data,
                                contain=['userid', 'resourceid', 'subjectcode', 'schoolstagecode', 'projectid', 'dt',
                                         'recommendation_index'],
                                table_name=rs_set.ALLDATA_TABLE, is_truncate=False, verbose=rs_set.VERBOSE)
        return

