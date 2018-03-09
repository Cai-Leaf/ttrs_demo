from surprise import SVD
from surprise import Dataset, Reader
import time
import numpy as np
import heapq
from ..settings.rs_course_setting import *
from collections import defaultdict


class UserCourseSVD:
    def __init__(self):
        self.__model = SVD(n_factors=100, n_epochs=1)

    def fit(self, user_course_score):
        reader = Reader(rating_scale=(1, 5))
        user_course_score = Dataset.load_from_df(user_course_score[['userid', 'courseid', 'score']], reader)
        user_course_score = user_course_score.build_full_trainset()
        self.__model.fit(user_course_score)

    def predict(self, user_course, rec_n, pre_type='quick'):
        result = []
        if pre_type == 'quick':
            for uid, candidate_list in user_course:
                in_uid = self.__model.trainset.to_inner_uid(uid)
                in_iid = [self.__model.trainset.to_inner_iid(course) for course in candidate_list]
                score = self.__model.trainset.global_mean + self.__model.bu[in_uid] + self.__model.bi[in_iid] + \
                        np.dot(self.__model.pu[in_uid], self.__model.qi[in_iid].T)
                score = heapq.nlargest(rec_n, [(candidate_list[score_i], score[score_i]) for score_i in range(len(score))],
                                       key=lambda k: k[1])
                result.append((uid, score))
            return result
        else:
            for uid, candidate_list in user_course:
                score = [(iid, self.__model.predict(uid, iid).est) for iid in candidate_list]
                score = heapq.nlargest(rec_n, score, key=lambda k: k[1])
                result.append((uid, score))
            return result


class UserOpenCourseCold:
    def __init__(self):
        self.__class_course_list = defaultdict(lambda: ClassCourseNode())

    def fit(self, user_course_score, user_info):
        # 统计各用户类别中课程的总分及总评分次数
        for uid, iid, r in user_course_score[['userid', 'courseid', 'score']].itertuples(index=False):
            if uid in user_info:
                user_msg = user_info[uid].split('-')
                cur_node = self.__class_course_list[user_msg[0]]
                cur_node.content[iid][0] += r
                cur_node.content[iid][1] += 1
                cur_node = cur_node.next[user_msg[1]]
                cur_node.content[iid][0] += r
                cur_node.content[iid][1] += 1
                cur_node = cur_node.next[user_msg[2]]
                cur_node.content[iid][0] += r
                cur_node.content[iid][1] += 1
        # 取各用户各类别中，平均分前的课程N
        for _, node in self.__class_course_list.items():
            tmp_list = [(iid, s_n[0] / s_n[1]) for iid, s_n in node.content.items()]
            node.content = heapq.nlargest(RECOMMEND_OPEN_COURSE_NUM, tmp_list, key=lambda k: k[1])
            for _, node2 in node.next.items():
                tmp_list = [(iid, s_n[0] / s_n[1]) for iid, s_n in node2.content.items()]
                node2.content = heapq.nlargest(RECOMMEND_OPEN_COURSE_NUM, tmp_list, key=lambda k: k[1])
                for _, node3 in node2.next.items():
                    tmp_list = [(iid, s_n[0] / s_n[1]) for iid, s_n in node3.content.items()]
                    node3.content = heapq.nlargest(RECOMMEND_OPEN_COURSE_NUM, tmp_list, key=lambda k: k[1])

    def predict(self, user_info):
        result = []
        for uid, class_name in user_info:
            result.append((uid, self.estimate(class_name)))
        return result

    def estimate(self, class_name):
        user_msg = class_name.split('-')
        result = []
        cur_node = self.__class_course_list[user_msg[0]]
        result.append(cur_node.content)
        cur_node = cur_node.next[user_msg[1]]
        result.append(cur_node.content)
        cur_node = cur_node.next[user_msg[2]]
        result.append(cur_node.content)
        for i in range(len(result) - 1, -1, -1):
            if len(result[i]) == RECOMMEND_OPEN_COURSE_NUM:
                return result[i]
        return result[0]


class ClassCourseNode:
    def __init__(self):
        self.content = defaultdict(lambda: [5 * 2.5, 5])
        self.next = defaultdict(lambda: ClassCourseNode())


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


