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
    'Anti Tracks is a complete solution to protect your privacy and enhance your PC performance. With a simple click Anti Tracks securely erase your internet tracks, computer activities and programs history information stored in many hidden files on your computer.Anti Tracks support Internet Explorer, AOL, Netscape/Mozilla and Opera browsers. It also include more than 85 free plug-ins to extend erasing features to support popular programs such as ACDSee, Acrobat Reader, KaZaA, PowerDVD, WinZip, iMesh, Winamp and much more.',
    """East-Tec Eraser goes beyond U.S. Department of Defense standards for the permanent erasure of digital information and easily removes every trace of sensitive data from your computer. Completely destroy information stored without your knowledge or approval: Internet history, Web pages and pictures from sites visited on the Internet, unwanted cookies, chatroom conversations, deleted e-mail messages, temporary files, the Windows swap file, the Recycle Bin, previously deleted files, valuable corporate trade secrets """,
    """and for other popular programs such as Windows Media Player, RealPlayer, Yahoo Messenger, ICQ, etc. Eraser has an intuitive interface and wizards that guide you through all the necessary steps needed to protect your privacy and sensitive information.Other features include support for custom privacy needs, user-defined erasure methods, command-line parameters, integration with Windows Explorer, and password protection.""",
    """GhostSurf Platinum ensures your safety online by providing an anonymous, encrypted Internet connection, and GhostSurf stops spyware, eliminates ads and erases your tracks. GhostSurf lets you customize your privacy level in real-time to suit your surfing needs. A variety of options enable you to block personal information, mask your IP address, route your data through anonymous hubs and even encrypt your Internet connection. GhostSurf's Privacy Control Center allows you to see and block every piece of data that your computer emits over the Internet, preventing even your Internet Service Provide""",
]*700
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
aaa = cosine_similarity(tfidf)
print(aaa[0, :])

