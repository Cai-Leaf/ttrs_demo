from collections import defaultdict
import heapq
import numpy as np
from ..settings.rs_resource_share_setting import *


class ClassRecommendModel:
    def __init__(self):
        self.class_iid_score = None
        return

    def fit(self, data):
        self.class_iid_score = defaultdict(lambda: defaultdict(float))
        for iid, pid, class_mame, score in data[['itemid', 'projectid', 'classname', 'score']].itertuples(index=False):
            self.class_iid_score[class_mame][iid] = score
        return

    def estimate(self, class_name, iid):
        if class_name not in self.class_iid_score:
            return 0
        return self.class_iid_score[class_name][iid]


class ResourceShareColdModel:
    def __init__(self):
        self.__class_course_list = defaultdict(lambda: ClassItemNode())
        return

    def fit(self, user_item, user_info):
        # 统计各用户类别中资源的总操作次数
        for uid, pid, iid in user_item[['userid', 'projectid', 'itemid']].itertuples(index=False):
            if uid in user_info:
                user_msg = user_info[uid].split('-')
                cur_node = self.__class_course_list[user_msg[0]]
                cur_node.content[iid] += 1
                cur_node = cur_node.next[user_msg[1]]
                cur_node.content[iid] += 1
                cur_node = cur_node.next[user_msg[2]]
                cur_node.content[iid] += 1
        return

    def predict(self, pre_data):
        result = []
        for uid, pid, class_name, candidate_list in pre_data:
            result.append((uid, pid, self.estimate(class_name, candidate_list)))
        return result

    def estimate(self, class_name, candidate_list):
        user_msg = class_name.split('-')
        # 取树的父节点到叶子节点
        cur_node = self.__class_course_list[user_msg[0]]
        item_score_0 = cur_node.content
        cur_node = cur_node.next[user_msg[1]]
        item_score_1 = cur_node.content
        cur_node = cur_node.next[user_msg[2]]
        item_score_2 = cur_node.content
        # 获取资源分数
        result = []
        for iid in candidate_list:
            if iid in item_score_2:
                result.append((iid, item_score_2[iid]))
                continue
            if iid in item_score_1:
                result.append((iid, item_score_1[iid]))
                continue
            result.append((iid, item_score_0[iid]))
        result = heapq.nlargest(MODEL1_RECOMMEND_NUM+MODEL2_RECOMMEND_NUM, result, key=lambda k: k[1])
        result = [iid for iid, _ in result]
        return result


class ClassItemNode:
    def __init__(self):
        self.content = defaultdict(int)
        self.next = defaultdict(lambda: ClassItemNode())


class ItemCollaborativeFiltering:
    def __init__(self):
        self.pid_mini_model = None
        return

    # 训练
    def fit(self, train_data):
        pid_train_data = defaultdict(list)
        # 划分子模型的训练集
        for uid, pid, iid in train_data[['userid', 'projectid', 'itemid']].itertuples(index=False):
            pid_train_data[pid].append((uid, iid))
        self.pid_mini_model = defaultdict(lambda: MiniItenModel())
        # 训练子模型
        for pid, mini_train_data in pid_train_data.items():
            mini_iid_num = len(set([iid for _, iid in mini_train_data]))
            if 8888 > mini_iid_num >= 5:
                self.pid_mini_model[pid].fit(mini_train_data)
        return

    def estimate(self, uid, pid, iid):
        if pid not in self.pid_mini_model:
            return 0
        return self.pid_mini_model[pid].estimate(uid, iid)


class MiniItenModel:
    def __init__(self):
        self.n_neighbor = 10
        self.inner_uid = None
        self.inner_iid = None
        self.user_itemlist = None
        self.sim = None
        return

    def fit(self, ui_data):
        # 构造训练所需的数据集
        self.construct_train_data(ui_data)
        # 根据Jaccard系数计算物品相似度 sim = |A∩B|/(|A|+|B|-|A∩B|)
        dim = len(self.inner_iid)
        count_x_y = np.zeros((dim, dim))
        count_x = np.zeros(dim)
        for _, items in self.user_itemlist.items():
            for i in range(len(items)):
                count_x_y[items[i]][items] += 1
                count_x[items[i]] += 1
        count_x = count_x.reshape((1, dim)).repeat(dim, axis=0)
        self.sim = count_x_y / (count_x + count_x.T - count_x_y + 1e-5)
        return

    def estimate(self, u, i):
        try:
            uid = self.inner_uid[u]
            iid = self.inner_iid[i]
        except KeyError:
            return 0
        # 计算相似度，取物品相似度和内容相似度的混合相似度
        i_n = len(self.user_itemlist[uid])
        iid_list = self.user_itemlist[uid]
        neighbor_sim = self.sim[iid][iid_list]
        # 取相似度最高的前n个值
        neighbor_sim = heapq.nlargest(self.n_neighbor, neighbor_sim)
        est = np.sum(neighbor_sim)/i_n
        return est

    def construct_train_data(self, ui_data):
        self.inner_uid = {}
        self.inner_iid = {}
        self.user_itemlist = defaultdict(list)

        current_u_index = 0
        current_i_index = 0

        for cuid, ciid in ui_data:
            try:
                uid = self.inner_uid[cuid]
            except KeyError:
                uid = current_u_index
                self.inner_uid[cuid] = current_u_index
                current_u_index += 1
            try:
                iid = self.inner_iid[ciid]
            except KeyError:
                iid = current_i_index
                self.inner_iid[ciid] = current_i_index
                current_i_index += 1
            self.user_itemlist[uid].append(iid)
        return


# 混合预测
def mix_predict(class_model, item_model, pre_data):
    result = []
    for uid, pid, candidate_list, class_iid_List in pre_data:
        # 使用协同过滤算法预测结果
        item_model_pre_result = [(iid, item_model.estimate(uid, pid, iid)) for iid in candidate_list]
        item_model_pre_result = heapq.nlargest(MODEL2_RECOMMEND_NUM, item_model_pre_result, key=lambda k: k[1])

        # 根据协同过滤的预测结果，删除类型候选表中的重复元素
        for iid, _ in item_model_pre_result:
            for _, iid_list, _ in class_iid_List:
                if iid in iid_list:
                    iid_list.remove(iid)

        # 使用类型算法预测结果
        class_model_pre_result = []
        for class_name, iid_list, num in class_iid_List:
            tmp_iid_score = [(iid, class_model.estimate(class_name, iid)) for iid in iid_list]
            tmp_iid_score = heapq.nlargest(num, tmp_iid_score, key=lambda k: k[1])
            class_model_pre_result += tmp_iid_score
        class_model_pre_result = sorted(class_model_pre_result, key=lambda k: k[1], reverse=True)

        # 结合两种算法的预测结果
        pre_result = []
        for i in range(max(len(item_model_pre_result), len(class_model_pre_result))):
            if i < len(item_model_pre_result):
                pre_result.append(item_model_pre_result[i][0])
            if i < len(class_model_pre_result):
                pre_result.append(class_model_pre_result[i][0])
        result.append((uid, pid, pre_result))
    return result
