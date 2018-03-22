from scipy import sparse, zeros
from collections import defaultdict
import heapq
import numpy as np


class UserCollaborativeFiltering:
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

    def predict(self, user_itemlist, item_score):
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
