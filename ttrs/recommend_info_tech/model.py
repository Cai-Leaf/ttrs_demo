from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
import heapq
from math import exp
import random
from ..settings.rs_info_tech_setting import RECOMMEND_NUM, RECOMMEND_NEW_NUM


class MixedCollaborativeFiltering:
    def __init__(self):
        self.n_neighbor = 10
        self.inner_uid = None
        self.inner_iid = None
        self.user_itemlist = None
        self.item_userlist = None
        self.item_content = None
        self.sim = None
        self.content_sim = None

    # 训练
    def fit(self, ui_data, i_msg_data):
        # 构造训练所需的数据集
        self.construct_train_data(ui_data[['userid', "itemid"]], i_msg_data)

        # 根据Jaccard系数计算物品相似度 sim = |A∩B|/(|A|+|B|-|A∩B|)
        dim = len(self.inner_iid)
        count_x_y = np.zeros((dim, dim))
        count_x = np.zeros(dim)

        for _, items in self.user_itemlist.items():
            for i in range(len(items)):
                count_x_y[items[i]][items] += 1
                count_x[items[i]] += 1
        count_x = count_x.reshape((1, dim)).repeat(dim, axis=0)
        self.sim = count_x_y / (count_x+count_x.T-count_x_y+1e-5)

        # 根据内容计算物品相似度
        # 将文本中的词语转换为词频矩阵, 计算个词语出现的次数
        vectorizer = CountVectorizer()
        cv = vectorizer.fit_transform(self.item_content)
        # 将词频矩阵X统计成TF-IDF值
        transformer = TfidfTransformer()
        tfidf = transformer.fit_transform(cv)
        # 计算cosine相似度
        self.content_sim = cosine_similarity(tfidf)
        return

    def predict(self, user_itemlist, item_score):
        result = []
        for uid, candidate_list, new_item_list in user_itemlist:
            score = self.batch_estimate(uid, candidate_list)
            score = heapq.nlargest(RECOMMEND_NUM, score, key=lambda k: k[1])
            new_score = [(iid, self.estimate_use_content_sim(uid, iid)) for iid in new_item_list]
            new_score = heapq.nlargest(RECOMMEND_NEW_NUM, new_score, key=lambda k: k[1])
            # 根据推荐度进行排序
            score = sorted([(iid, item_score[iid]) for iid, _ in score], key=lambda k: k[1], reverse=True)
            # 将新物品随机插入推荐列表1/3到2/3的位置
            for new_item in new_score:
                index = random.randint(len(score)//3, len(score)//3*2)
                score.insert(index, new_item)
            result.append((uid, score))
        return result

    def estimate(self, u, i):
        try:
            uid = self.inner_uid[u]
            iid = self.inner_iid[i]
        except KeyError:
            return 0
        # 计算相似度，取物品相似度和内容相似度的混合相似度
        i_n = len(self.user_itemlist[uid])
        iid_list = self.user_itemlist[uid]
        a = 1/(1+exp(-(i_n-5)))
        neighbor_sim = a*self.sim[iid][iid_list]+(1-a)*self.content_sim[iid][iid_list]
        # 取相似度最高的前n个值
        neighbor_sim = heapq.nlargest(self.n_neighbor, neighbor_sim)
        est = np.sum(neighbor_sim)/i_n
        return est

    def batch_estimate(self, u, i_list):
        if u not in self.inner_uid:
            return []
        uid = self.inner_uid[u]
        real_iid = []
        real_inner_iid = []
        for i in i_list:
            if i in self.inner_iid:
                real_iid.append(i)
                real_inner_iid.append(self.inner_iid[i])
        i_n = len(self.user_itemlist[uid])
        iid_list = self.user_itemlist[uid]
        a = 1 / (1 + exp(-(i_n - 5)))
        neighbor_sim = a * self.sim[real_inner_iid][:, iid_list] + (1 - a) * self.content_sim[real_inner_iid][:, iid_list]
        if i_n < self.n_neighbor:
            neighbor_sim = np.sum(neighbor_sim, axis=1)/i_n
            est = [(real_iid[i], neighbor_sim[i]) for i in range(len(real_iid))]
            return est
        else:
            est = []
            for i in range(len(neighbor_sim)):
                tmp_score = neighbor_sim[i]
                tmp_score = np.sum(tmp_score[np.argpartition(tmp_score, -self.n_neighbor)[-self.n_neighbor:]])/self.n_neighbor
                est.append(tmp_score)
            est = [(real_iid[i], est[i]) for i in range(len(real_iid))]
            return est

    def estimate_use_content_sim(self, u, i):
        try:
            uid = self.inner_uid[u]
            iid = self.inner_iid[i]
        except KeyError:
            return 0
        i_n = len(self.user_itemlist[uid])
        uid_list = self.user_itemlist[uid]
        neighbor_sim = self.content_sim[iid][uid_list]
        neighbor_sim = heapq.nlargest(self.n_neighbor, neighbor_sim)
        est = np.sum(neighbor_sim) / i_n
        return est

    def construct_train_data(self, ui_data, i_msg_data):
        self.inner_uid = {}
        self.inner_iid = {}
        self.user_itemlist = defaultdict(list)
        self.item_userlist = defaultdict(list)

        current_u_index = 0
        current_i_index = 0

        for ciid in i_msg_data['itemid']:
            if ciid not in self.inner_iid:
                self.inner_iid[ciid] = current_i_index
                current_i_index += 1

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
            self.user_itemlist[uid].append(iid)
            self.item_userlist[iid].append(uid)

        self.item_content = ['']*len(self.inner_iid)
        for ciid, content in i_msg_data.itertuples(index=False):
            self.item_content[self.inner_iid[ciid]] = content
        return

    # def old_predict(self, user_itemlist, item_score):
    #     result = []
    #     i = 0
    #     for uid, candidate_list, new_item_list in user_itemlist:
    #         score = [(iid, self.estimate(uid, iid)) for iid in candidate_list]
    #         score = heapq.nlargest(RECOMMEND_NUM, score, key=lambda k: k[1])
    #         new_score = [(iid, self.estimate_use_content_sim(uid, iid)) for iid in new_item_list]
    #         new_score = heapq.nlargest(RECOMMEND_NEW_NUM, new_score, key=lambda k: k[1])
    #         # 根据推荐度进行排序
    #         score = sorted([(iid, item_score[iid]) for iid, _ in score], key=lambda k: k[1], reverse=True)
    #         # 将新物品随机插入推荐列表1/3到2/3的位置
    #         for new_item in new_score:
    #             index = random.randint(len(score) // 3, len(score) // 3 * 2)
    #             score.insert(index, new_item)
    #         result.append((uid, score))
    #     return result


class InfoTechColdModel:
    def __init__(self):
        self.__class_item_list = None
        self.__default_result = None
        return

    def fit(self, ui_data, user_info):
        # 统计各用户类别中物品的总分及总评分次数
        item_count = defaultdict(int)
        self.__class_item_list = defaultdict(lambda: ClassItemNode())
        for uid, iid in ui_data[['userid', 'itemid']].itertuples(index=False):
            if uid in user_info:
                item_count[iid] += 1
                user_msg = user_info[uid].split('-')
                cur_node = self.__class_item_list[user_msg[0]]
                cur_node.content[iid] += 1
                cur_node = cur_node.next[user_msg[1]]
                cur_node.content[iid] += 1
                cur_node = cur_node.next[user_msg[2]]
                cur_node.content[iid] += 1
        # 取各用户各类别中，点击次数前n的物品
        self.__default_result = heapq.nlargest(RECOMMEND_NUM, item_count.items(), key=lambda k: k[1])
        for _, node in self.__class_item_list.items():
            node.content = heapq.nlargest(RECOMMEND_NUM, node.content.items(), key=lambda k: k[1])
            # 进入第二层树结构
            for _, node2 in node.next.items():
                node2.content = heapq.nlargest(RECOMMEND_NUM, node2.content.items(), key=lambda k: k[1])
                # 进入第三层树结构
                for _, node3 in node2.next.items():
                    node3.content = heapq.nlargest(RECOMMEND_NUM, node3.content.items(), key=lambda k: k[1])

        # for name, node in self.__class_item_list.items():
        #     print(name, len(node.content))
        #     # 进入第二层树结构
        #     for name2, node2 in node.next.items():
        #         print(name, name2, len(node2.content))
        #         # 进入第三层树结构
        #         for name3, node3 in node2.next.items():
        #             print(name, name2, name3, len(node3.content))

        return

    def predict(self, data):
        result = []
        for uid, class_name, new_item_list in data:
            tmp_result = self.estimate(class_name)
            # 将新物品随机插入推荐列表1/3到2/3的位置
            for new_item in new_item_list:
                index = random.randint(len(tmp_result) // 3, len(tmp_result) // 3 * 2)
                tmp_result.insert(index, (new_item, 0))
            result.append((uid, tmp_result))
        return result

    def estimate(self, class_name):
        user_msg = class_name.split('-')
        # 取树的父节点到叶子节点
        content = []
        cur_node = self.__class_item_list[user_msg[0]]
        content.append(cur_node.content)
        cur_node = cur_node.next[user_msg[1]]
        content.append(cur_node.content)
        cur_node = cur_node.next[user_msg[2]]
        content.append(cur_node.content)
        # 获取课程分数
        for result in content[::-1]:
            if len(result) == RECOMMEND_NUM:
                return result
        return self.__default_result.copy()


class ClassItemNode:
    def __init__(self):
        self.content = defaultdict(int)
        self.next = defaultdict(lambda: ClassItemNode())
        return
