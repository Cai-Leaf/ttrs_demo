from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
import heapq
from math import exp


class MixedCollaborativeFiltering:
    def __init__(self, n_neighbor):
        self.n_neighbor = n_neighbor
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

    def predict(self, user_itemlist):
        result = []
        for uid, candidate_list in user_itemlist:
            score = [(iid, self.estimate(uid, iid)) for iid in candidate_list]
            score = heapq.nlargest(20, score, key=lambda k: k[1])
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

