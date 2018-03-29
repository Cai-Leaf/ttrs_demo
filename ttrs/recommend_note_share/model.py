import jieba
import re
import heapq
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

    def predict(self, predata, item_score):
        result = []
        for uid, pid, near_item, pre_num, candidate_list in predata:
            result_item = set()
            for iid in near_item:
                sim_item = self.estimate(pid, iid, candidate_list)
                num = pre_num
                for sim_iid in sim_item:
                    if sim_iid not in result_item:
                        result_item.add(sim_iid)
                        num -= 1
                    if num <= 0:
                        break
            sim_item = [(iid, item_score[iid]) for iid in result_item]
            sim_item = sorted(sim_item, key=lambda k: k[1], reverse=True)
            result.append((uid, pid, sim_item))
        return

    def estimate(self, pid, item_id, candidate_list):
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
        result = sorted(result, key=lambda k: k[1], reverse=True)
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


class NoteShareColdModel:
    def __init__(self):
        self.item_score = None

    def fit(self, item_score):
        self.item_score = item_score

    def predict(self, pre_data):
        result = []
        for uid, pid, candidate_list in pre_data:
            score = [(iid, self.item_score[iid]) for iid in candidate_list]
            score = heapq.nlargest(10, score, key=lambda k: k[1])
            score = [iid for iid, _ in score]
            result.append((uid, pid, score))
        return
