from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
import heapq
from math import exp


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
        for uid, candidate_list in user_itemlist:
            score = [(iid, self.estimate(uid, iid)) for iid in candidate_list]
            score = heapq.nlargest(20, score, key=lambda k: k[1])
            # 根据推荐度进行排序
            score = sorted([(iid, item_score[iid]) for iid, _ in score], key=lambda k: k[1], reverse=True)
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
        uid_list = self.user_itemlist[uid]
        a = 1/(1+exp(-(i_n-5)))
        neighbor_sim = a*self.sim[iid][uid_list]+(1-a)*self.content_sim[iid][uid_list]
        # 取相似度最高的前n个值
        neighbor_sim = heapq.nlargest(self.n_neighbor, neighbor_sim)
        est = np.sum(neighbor_sim)/i_n
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


class InfoTechColdModel:
    def __init__(self):
        self.__class_item_list = None
        self.__default_result = None
        return

    def fit(self, ui_data, user_info):
        # 统计各用户类别中课程的总分及总评分次数
        item_count = defaultdict(int)
        for uid, iid in ui_data[['userid', 'courseid']].itertuples(index=False):
            if uid in user_info:
                item_count[iid] += 1
                user_msg = user_info[uid].split('-')
                cur_node = self.__class_item_list[user_msg[0]]
                cur_node.content[iid] += 1
                cur_node = cur_node.next[user_msg[1]]
                cur_node.content[iid] += 1
                cur_node = cur_node.next[user_msg[2]]
                cur_node.content[iid] += 1
        # 取各用户各类别中，平均分前的课程N, 并重构node节点的内容
        self.__default_result = heapq.nlargest(10, item_count.items(), key=lambda k: k[1])
        for _, node in self.__class_item_list.items():
            node.content = heapq.nlargest(10, node.content.items(), key=lambda k: k[1])
            # 进入第二层树结构
            for _, node2 in node.next.items():
                node2.content = heapq.nlargest(10, node2.content.items(), key=lambda k: k[1])
                # 进入第三层树结构
                for _, node3 in node2.next.items():
                    node3.content = heapq.nlargest(10, node3.content.items(), key=lambda k: k[1])
        return

    def predict(self, data):
        result = []
        for uid, class_name in data:
            result.append((uid, self.estimate(class_name)))
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
            if len(result) == 10:
                return result
        return self.__default_result


class ClassItemNode:
    def __init__(self):
        self.content = defaultdict(int)
        self.next = defaultdict(lambda: ClassItemNode())
        return
