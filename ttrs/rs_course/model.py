from surprise import SVD
from surprise import Dataset, Reader
import time
import numpy as np
import heapq
from ..settings.course_rs_setting import *


class UserCourseSVD:
    def __init__(self):
        self.__model = SVD(n_factors=100, n_epochs=1)

    def fit(self, user_course_score):
        reader = Reader(rating_scale=(1, 5))
        user_course_score = Dataset.load_from_df(user_course_score[['userid', 'courseid', 'score']], reader)
        user_course_score = user_course_score.build_full_trainset()
        self.__model.fit(user_course_score)

    def predict(self, user_course, pre_type='quick'):
        result = []
        if pre_type == 'quick':
            for uid, candidate_list in user_course:
                in_uid = self.__model.trainset.to_inner_uid(uid)
                in_iid = [self.__model.trainset.to_inner_iid(course) for course in candidate_list]
                score = self.__model.trainset.global_mean + self.__model.bu[in_uid] + self.__model.bi[in_iid] + \
                        np.dot(self.__model.pu[in_uid], self.__model.qi[in_iid].T)
                score = heapq.nlargest(RECOMMEND_COURSE_NUM, [(candidate_list[score_i], score[score_i]) for score_i in range(len(score))],
                                       key=lambda k: k[1])
                result.append((uid, score))
            return result
        else:
            for uid, candidate_list in user_course:
                score = [(iid, self.__model.predict(uid, iid).est) for iid in candidate_list]
                score = heapq.nlargest(RECOMMEND_COURSE_NUM, score, key=lambda k: k[1])
                result.append((uid, score))
            return result


class UserOpenCourseCold:
    def __init__(self):
        self.__class_course_list = {}

    def fit(self, user_course_score, user_info):
        # 统计各用户类别中课程的总分及总评分次数
        class_course_score = {"class-other": dict()}
        for uid, iid, r in user_course_score[['userid', 'courseid', 'score']].itertuples(index=False):
            if uid in user_info:
                if user_info[uid] in class_course_score:
                    if iid in class_course_score[user_info[uid]]:
                        class_course_score[user_info[uid]][iid][0] += r
                        class_course_score[user_info[uid]][iid][1] += 1
                    else:
                        class_course_score[user_info[uid]][iid] = [r, 5]
                else:
                    class_course_score[user_info[uid]] = {iid: [r, 5]}
            else:
                if iid in class_course_score["class-other"]:
                    class_course_score["class-other"][iid][0] += r
                    class_course_score["class-other"][iid][1] += 1
                else:
                    class_course_score["class-other"][iid] = [r, 5]
        # 将各用户类别中，平均分最大的前20门课程保存到模型中
        for class_name, course_dict in class_course_score.items():
            tmp_course_list = [(courseid, course_score[0] / course_score[1]) for courseid, course_score in
                               course_dict.items()]
            tmp_course_list = heapq.nlargest(RECOMMEND_COURSE_NUM, tmp_course_list, key=lambda k: k[1])
            self.__class_course_list[class_name] = tmp_course_list

    def predict(self, user_info):
        result = []
        for uid, class_name in user_info:
            result.append((uid, self.__class_course_list[class_name]))
        return result


class UserElectiveCourseCold:
    def __init__(self):
        self.__course_score = {}

    def fit(self, user_course_score):
        # 统计课程的总分及总评分次数
        for _, iid, r in user_course_score[['userid', 'courseid', 'score']].itertuples(index=False):
            if iid in self.__course_score:
                self.__course_score[iid][0] += r
                self.__course_score[iid][1] += 1
            else:
                self.__course_score[iid] = [r, 20]
        # 将总评分及总次数转化成平均分
        for iid, score_count in self.__course_score.items():
            self.__course_score[iid] = score_count[0] / score_count[1]

    def predict(self, user_course):
        result = []
        for uid, candidate_list in user_course:
            score = [(iid, self.__course_score.get(iid, 2.5)) for iid in candidate_list]
            score = heapq.nlargest(RECOMMEND_COURSE_NUM, score, key=lambda k: k[1])
            result.append((uid, score))
        return result


