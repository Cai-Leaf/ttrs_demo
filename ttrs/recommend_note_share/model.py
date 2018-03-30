import jieba
import re
import heapq
import numpy as np
from ..settings.rs_note_share_setting import CF_RECOMMEND_NUM, CONTENT_RECOMMEND_NUM
from collections import defaultdict
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ContentSimilarityModel:
    def __init__(self):
        self.pid_sim = None
        return

    def fit(self, item_content):
        # 构造projectid对应的itemid，itemid对应的内部id
        pid_iid_list = defaultdict(list)
        inner_iid = defaultdict(int)

        # 构造语料库
        corpus = []
        cur_index = 0

        # 构造正则表达式与停用词表，去除文本中的特殊符号
        flag_word = r"[\s+\.\!\/_,$?%^*()<>+\"\';:1234567890]+|[——！，。？、~@#￥%……&*（）《》；【】“”：:]+"
        html_word = r'<[^>]+>'
        stop_word = {'quot', ' ', 'nbsp'}
        flag_dr = re.compile(flag_word)
        html_dr = re.compile(html_word)

        for iid, pid, content in item_content.itertuples(index=False):
            pid_iid_list[pid].append(iid)
            inner_iid[iid] = cur_index
            cur_index += 1
            # 去除文本中的特殊符号
            content = html_dr.sub(' ', content)
            content = flag_dr.sub(' ', content)
            content = jieba.cut(content)
            content = " ".join([word for word in content if word not in stop_word and len(word) > 1])
            corpus.append(content)

        # 将文本中的词语转换为词频矩阵
        vectorizer = CountVectorizer().fit_transform(corpus)
        # 将词频矩阵X统计成TF-IDF值
        tf_idf = TfidfTransformer().fit_transform(vectorizer)

        # 构造相似度映射矩阵
        self.pid_sim = defaultdict(lambda: ContentSimilarity())
        for pid, iid_list in pid_iid_list.items():
            if 8888 > len(iid_list) > 10:
                inner_index = [inner_iid[iid] for iid in iid_list]
                self.pid_sim[pid].construct_similarity(iid_list, tf_idf[inner_index])
        return

    def estimate(self, pid, item_id, pre_num, candidate_list):
        if pid not in self.pid_sim:
            return []
        content_similarity = self.pid_sim[pid]
        if item_id not in content_similarity.inner_iid:
            return []
        inner_iid_dict = content_similarity.inner_iid
        real_iid = []
        inner_iid = []
        for iid in candidate_list:
            if iid in inner_iid_dict:
                real_iid.append(iid)
                inner_iid.append(inner_iid_dict[iid])
        score = content_similarity.sim[inner_iid_dict[item_id]][inner_iid]
        result = [(real_iid[i], score[i]) for i in range(len(real_iid))]
        result = heapq.nlargest(pre_num, result, key=lambda k: k[1])
        result = [iid for iid, _ in result]
        return result


class ContentSimilarity:
    def __init__(self):
        self.inner_iid = None
        self.sim = None
        return

    def construct_similarity(self, iid_list, tfidf):
        self.inner_iid = defaultdict(int)
        for i in range(len(iid_list)):
            self.inner_iid[iid_list[i]] = i
        self.sim = cosine_similarity(tfidf)
        return


class NoteCollaborativeFiltering:
    def __init__(self):
        self.pid_mini_model = None
        return

    # 训练
    def fit(self, train_data):
        pid_train_data = defaultdict(list)
        # 划分子模型的训练集
        for uid, pid, iid in train_data[['userid', 'projectid', 'itemid']].itertuples(index=False):
            pid_train_data[pid].append((uid, iid))
        self.pid_mini_model = defaultdict(lambda: MiniNoteModel())
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

    def batch_estimate(self, uid, pid, iid_list):
        if pid not in self.pid_mini_model:
            return []
        return self.pid_mini_model[pid].batch_estimate(uid, iid_list)


class MiniNoteModel:
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
        est = np.sum(neighbor_sim) / i_n
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
        neighbor_sim = self.sim[real_inner_iid][:, iid_list]
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


class NoteShareColdModel:
    def __init__(self):
        self.pid_result = None

    def fit(self, item_projectid_score):
        pid_iid_score = defaultdict(list)
        for iid, pid, score in item_projectid_score.itertuples(index=False):
            pid_iid_score[pid].append((iid, score))
        self.pid_result = defaultdict(list)
        for pid, iid_score_list in pid_iid_score.items():
            iid_score_list = heapq.nlargest(CF_RECOMMEND_NUM+CONTENT_RECOMMEND_NUM, iid_score_list, key=lambda k: k[1])
            iid_score_list = [iid for iid, _ in iid_score_list]
            self.pid_result[pid] = iid_score_list
        return

    def predict(self, pre_data):
        result = []
        for uid, pid in pre_data:
            result.append((uid, pid, self.pid_result[pid]))
        return result


def mix_predict(content_model, cf_model, pre_data, item_score):
    result = []
    for uid, pid, near_item, pre_num, candidate_list in pre_data:
        # 使用基于内容的模型预测
        content_model_pre_result = set()
        for iid in near_item:
            candidate_list -= content_model_pre_result
            sim_item = content_model.estimate(pid, iid, pre_num, candidate_list)
            content_model_pre_result = content_model_pre_result | set(sim_item)
        # 使用协同过滤模型预测
        candidate_list -= content_model_pre_result
        # cf_model_pre_result = [(iid, cf_model.estimate(uid, pid, iid)) for iid in candidate_list]
        cf_model_pre_result = cf_model.batch_estimate(uid, pid, candidate_list)
        cf_model_pre_result = heapq.nlargest(CF_RECOMMEND_NUM, cf_model_pre_result, key=lambda k: k[1])
        cf_model_pre_result = set([iid for iid, _ in cf_model_pre_result])
        # 结合内容和协同过滤模型的预测结果
        result_item = [(iid, item_score[iid]) for iid in content_model_pre_result | cf_model_pre_result]
        result_item = sorted(result_item, key=lambda k: k[1], reverse=True)
        result_item = [iid for iid, _ in result_item]
        result.append((uid, pid, result_item))
    return result
