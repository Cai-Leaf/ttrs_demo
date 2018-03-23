from scipy import sparse, zeros
from collections import defaultdict
import heapq
import numpy as np


class ClassRecommendModel:
    def __init__(self):
        self.class_iid_score = None
        return

    def fit(self, data):
        self.class_iid_score = defaultdict(lambda: defaultdict(float))
        for iid, pid, class_mame, score in data[['itemid', 'projectid', 'classname', 'score']].itertuples(index=False):
            self.class_iid_score[class_mame][real_id(pid, iid)] = score
        return

    def predict(self, pre_data):
        result = []
        for uid, pid, class_iid_List, in pre_data:
            iid_score = []
            for class_name, iid_list, num in class_iid_List:
                tmp_iid_score = [(iid, self.class_iid_score[class_name][real_id(pid, iid)]) for iid in iid_list]
                tmp_iid_score = heapq.nlargest(num, tmp_iid_score, key=lambda k: k[1])
                iid_score += tmp_iid_score
            iid_score = sorted(iid_score,  key=lambda k: k[1], reverse=True)
            result.append((uid, pid, iid_score))
        return result

    def estimate(self, class_name, pid, iid):
        score = self.class_iid_score[class_name][real_id(pid, iid)]
        return score


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
                cur_node.content[real_id(pid, iid)] += 1
                cur_node = cur_node.next[user_msg[1]]
                cur_node.content[real_id(pid, iid)] += 1
                cur_node = cur_node.next[user_msg[2]]
                cur_node.content[real_id(pid, iid)] += 1
        return

    def predict(self, pre_data):
        result = []
        for uid, pid, class_name, candidate_list in pre_data:
            result.append((uid, pid, self.estimate(pid, class_name, candidate_list)))
        return

    def estimate(self, pid, class_name, candidate_list):
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
                result.append((iid, item_score_2[real_id(pid, iid)]))
                continue
            if iid in item_score_1:
                result.append((iid, item_score_1[real_id(pid, iid)]))
                continue
            result.append((iid, item_score_0[real_id(pid, iid)]))
        result = heapq.nlargest(10, result, key=lambda k: k[1])
        return result


class ClassItemNode:
    def __init__(self):
        self.content = defaultdict(int)
        self.next = defaultdict(lambda: ClassItemNode())


class ItemCollaborativeFiltering:
    def __init__(self):
        self.n_neighbor = 10
        self.inner_uid = None
        self.inner_iid = None
        self.item_userlist = None
        self.sim = None

    # 训练
    def fit(self, ui_data):
        # 构造训练所需的数据集
        self.construct_train_data(ui_data[['userid', "itemid"]])

        # 根据Jaccard系数计算用户相似度 sim = |A∩B|/(|A|+|B|-|A∩B|)
        dim = len(self.inner_uid)
        count_x_y = sparse.lil_matrix((dim, dim))
        count_x = zeros(dim)
        print(len(self.item_userlist))

        for iid, users in self.item_userlist.items():
            u_len = len(users)
            for i in range(u_len):
                count_x_y[users[i], users] += np.ones((1, u_len))
                count_x[users[i]] += 1
            print(u_len)
        for i in range(dim):
            for j in range(dim):
                n = count_x[i] + count_x[j] - count_x_y[i, j]
                if n > 0:
                    count_x_y[i, j] /= n
        self.sim = count_x_y.tocsr()
        return

    def predict(self, user_itemlist):
        return

    def estimate(self, u, i):
        try:
            uid = self.inner_uid[u]
            iid = self.inner_iid[i]
        except KeyError:
            return 0

        uid_list = self.item_userlist[iid]
        print(uid_list)
        est = self.sim[uid, uid_list].toarray()
        est = heapq.nlargest(10, est[est > 0])
        if len(est) == 0:
            return 0
        est = np.sum(est)/len(est)
        return est

    def construct_train_data(self, ui_data):
        self.inner_uid = {}
        self.inner_iid = {}
        self.item_userlist = defaultdict(list)

        current_u_index = 0
        current_i_index = 0

        for cuid, ciid in ui_data.itertuples(index=False):
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

            self.item_userlist[iid].append(uid)
        return


# 混合预测
def mix_predict(class_model, item_model, pre_data):
    result = []
    for uid, pid, candidate_list, class_iid_List in pre_data:
        # 使用协同过滤算法预测结果
        item_model_pre_result = [(iid, item_model.estimate(uid, uid)) for iid in candidate_list]
        item_model_pre_result = heapq.nlargest(5, item_model_pre_result, key=lambda k: k[1])

        # 根据协同过滤的预测结果，删除类型候选表中的重复元素
        for iid, _ in item_model_pre_result:
            for _, iid_list, _ in class_iid_List:
                if iid in iid_list:
                    iid_list.remove(iid)

        # 使用类型算法预测结果
        class_model_pre_result = []
        for class_name, iid_list, num in class_iid_List:
            tmp_iid_score = [(iid, class_model.estimate(class_name, pid, iid)) for iid in iid_list]
            tmp_iid_score = heapq.nlargest(num, tmp_iid_score, key=lambda k: k[1])
            class_model_pre_result += tmp_iid_score
        class_model_pre_result = sorted(class_model_pre_result, key=lambda k: k[1], reverse=True)

        # 结合两种算法的预测结果
        pre_result = []
        for i in range(max(len(item_model_pre_result), len(class_model_pre_result))):
            if i < len(item_model_pre_result):
                pre_result.append(item_model_pre_result[i])
            if i < len(class_model_pre_result):
                pre_result.append(class_model_pre_result[i])

        result.append((uid, pid, pre_result))
    return result


def real_id(pid, iid):
    return str(int(pid))+'-'+str(int(iid))
