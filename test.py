import datetime
from collections import defaultdict
import random
import numpy as np
from scipy import sparse, zeros
import scipy
import heapq
import pandas as pd
from ttrs.recommend_resource_share.model import ItemCollaborativeFiltering
from numpy.random import rand


# a = 30
# now_time = datetime.datetime.now()
# yes_time = now_time + datetime.timedelta(days=-a)
# print('"' + yes_time.strftime('%Y-%m-%d') + '"')



# data = pd.read_csv('./data/user_score_test2.csv', header=0)
# data = data[['userid', 'courseid']]
# data.rename(columns={'courseid': 'itemid'}, inplace=True)
# print(len(data))
# print(len(set(data['itemid'].values)))
# print(data.info())
# model = UserCollaborativeFiltering()
# model.fit(data)
# n = 0
# for iid, ulist in model.item_userlist.items():
#     n += len(ulist)
# print(n/len(model.item_userlist))
# print(len(model.item_userlist))
# print(model.estimate(0, 3))
from sklearn.feature_extraction.text import CountVectorizer
# 语料
corpus = [
    "我 啊 呵呵 么么哒 什么",
    "你 啊 呵呵 高效 什么",
    "你 名 呵呵 高效 不知道",
    "它 时 呵呵 道理 不知道"
    ]*100
# 将文本中的词语转换为词频矩阵
vectorizer = CountVectorizer()
# 计算个词语出现的次数
X = vectorizer.fit_transform(corpus)
# 获取词袋中所有文本关键词
word = vectorizer.get_feature_names()


from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 类调用
transformer = TfidfTransformer()
# 将词频矩阵X统计成TF-IDF值
tfidf = transformer.fit_transform(X)
# 查看数据结构 tfidf[i][j]表示i类文本中的tf-idf权重
aaa = cosine_similarity(tfidf[[0, 3, 5, 6]])
print(aaa)

