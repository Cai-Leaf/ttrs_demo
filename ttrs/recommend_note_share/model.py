import jieba
import re
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

        for iid, pid, content in item_content:
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
            if len(iid_list) > 10:
                inner_index = [inner_iid[iid] for iid in iid_list]
                self.pid_sim[pid].construct_similarity(iid_list, tf_idf[inner_index])
        return


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
