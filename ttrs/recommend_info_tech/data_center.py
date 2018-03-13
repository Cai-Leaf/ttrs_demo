from ..utils import db_data
from collections import defaultdict
import datetime


class InfoTechDataManager:
    def __init__(self):
        self.__user_item_data = None
        self.__user_info = None
        self.__user_projectid_list = None
        return

    def load_user_item_data(self):
        if self.__user_item_data is None:
            self.__user_item_data = db_data.read_db_to_df(sql="default",
                                                          contain=['userid', 'itemid'],
                                                          info='user_item',
                                                          verbose=True)
        return

    # 加载(用户信息)数据，处理成(用户ID-用户类型)
    def load_user_info(self):
        if self.__user_info is None:
            # data = pd.read_csv("./data/user_info.csv", header=0)
            contain_name = ['userid', 'projectid', 'age', 'gender', 'schoolstagecode', 'subjectcode']
            data = db_data.read_db_to_df(sql="", contain=contain_name,
                                         info="", verbose="")
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

    def get_user_item_data(self):
        if self.__user_item_data is None:
            self.load_user_item_data()
        return self.__user_item_data

    def get_item_msg_data(self):
        result = db_data.read_db_to_df(sql="default",
                                       contain=['userid', 'courseid'],
                                       info='user_item',
                                       verbose=True)
        return result

    def get_item_score(self):
        item_score = db_data.read_db_to_df(sql="default",
                                           contain=['itemid', 'socre'],
                                           info='item_score',
                                           verbose=True)
        result = defaultdict(lambda: 40.0)
        for iid, score in item_score.itertuples(index=False):
            result[iid] = score
        return result

    def get_user_info(self):
        if self.__user_info is None:
            self.load_user_info()
        return self.__user_info

    # 构造用户信息技术技巧大全推荐集合
    # 选取在(用户ID-用户类型)和(用户ID-物品ID)中同时出现的用户
    def get_pre_data(self):
        if self.__user_info is None:
            self.load_user_info()
        if self.__user_item_data is None:
            self.load_user_item_data()
        # 构造信息技术技巧大全推荐集合
        item_list = set(self.__user_item_data['itemid'].values)
        # 根据用户有过选课及浏览记录的课程构造过滤表
        filter_list = self.make_item_filter()
        pre_data = []
        for uid in set(self.__user_item_data['userid'].values):
            if uid in self.__user_info:
                candidate_list = list(item_list - filter_list[uid])
                if len(candidate_list) > 0:
                    pre_data.append((uid, candidate_list))
        return pre_data

    # 构造冷启动用户信息技术技巧大全推荐集合
    # 选取在(用户ID-用户类型)出现但在(用户ID-物品ID)没有出现的用户
    def get_cold_pre_data(self):
        if self.__user_info is None:
            self.load_user_info()
        if self.__user_item_data is None:
            self.load_user_item_data()
        tmp_user_id = set(self.__user_item_data['userid'].values)
        cold_pre_data = []
        for uid, info in self.__user_info.tems():
            if uid not in tmp_user_id:
                cold_pre_data.append((uid, info))
        return cold_pre_data

    def save_to_db(self, data):
        if self.__user_info is None:
            self.load_user_info()

        table_name = ""
        alldata_table_name = ""
        stay_table_name = ""

        time = datetime.datetime.now().strftime('%Y-%m-%d')
        save_data = []
        uid_list = set()
        for uid, item_list in data:
            if len(item_list) > 0:
                uid_list.add(uid)
                tmp_ssc_sc = self.__user_info[uid].split('-')[0].split('*')
                ssc = tmp_ssc_sc[0]
                sc = tmp_ssc_sc[1]
                item_num = len(item_list)
                for i in range(item_num):
                    iid = item_list[i][0]
                    score = i*(100-80)/(item_num-1)+80
                    for projectid in self.__user_projectid_list[uid]:
                        save_data.append((uid, iid, sc, ssc, projectid, time, score))
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

    def make_item_filter(self):
        if self.__user_item_data is None:
            self.load_user_item_data()
        filter_list = defaultdict(set)
        for uid, iid, in self.__user_item_data.itertuples(index=False):
            filter_list[uid].add(iid)
        return filter_list



