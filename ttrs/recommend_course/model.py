from surprise import SVD
from surprise import Dataset, Reader
import numpy as np
import heapq
from ..settings.rs_course_setting import *
from collections import defaultdict


class UserCourseSVD:
    def __init__(self):
        self.__model = SVD(n_factors=32, n_epochs=20)

    def fit(self, user_course_score):
        reader = Reader(rating_scale=(1, 5))
        user_course_score = Dataset.load_from_df(user_course_score[['userid', 'courseid', 'score']], reader)
        user_course_score = user_course_score.build_full_trainset()
        self.__model.fit(user_course_score)

    def predict(self, user_course, rec_n, pre_type='quick'):
        result = []
        if pre_type == 'quick':
            for uid, projectid, activiesid, course_package_id, candidate_list in user_course:
                in_uid = self.__model.trainset.to_inner_uid(uid)
                in_iid = [self.__model.trainset.to_inner_iid(course) for course in candidate_list]
                score = self.__model.trainset.global_mean + self.__model.bu[in_uid] + self.__model.bi[in_iid] + \
                        np.dot(self.__model.pu[in_uid], self.__model.qi[in_iid].T)
                score = heapq.nlargest(rec_n, [(candidate_list[score_i], score[score_i]) for score_i in range(len(score))],
                                       key=lambda k: k[1])
                result.append((uid, projectid, activiesid, course_package_id, score))
            return result
        else:
            for uid, projectid, activiesid, course_package_id, candidate_list in user_course:
                score = [(iid, self.__model.predict(uid, iid).est) for iid in candidate_list]
                score = heapq.nlargest(rec_n, score, key=lambda k: k[1])
                result.append((uid, projectid, activiesid, course_package_id, score))
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
        # 重构node节点的内容,将其表示为平均分
        for _, node in self.__class_course_list.items():
            tmp_list = [(iid, s_n[0] / s_n[1]) for iid, s_n in node.content.items()]
            node.content = defaultdict(lambda: 0)
            for iid, score in tmp_list:
                node.content[iid] = score
            # 进入第二层树结构
            for _, node2 in node.next.items():
                tmp_list = [(iid, s_n[0] / s_n[1]) for iid, s_n in node2.content.items()]
                node2.content = defaultdict(lambda: 0)
                for iid, score in tmp_list:
                    node2.content[iid] = score
                # 进入第三层树结构
                for _, node3 in node2.next.items():
                    tmp_list = [(iid, s_n[0] / s_n[1]) for iid, s_n in node3.content.items()]
                    node3.content = defaultdict(lambda: 0)
                    for iid, score in tmp_list:
                        node3.content[iid] = score

    def predict(self, user_info):
        result = []
        for uid, projectid, class_name, candidate_list in user_info:
            result.append((uid, projectid, "", "", self.estimate(class_name, candidate_list)))
        return result

    def estimate(self, class_name, candidate_list):
        user_msg = class_name.split('-')
        # 取树的父节点到叶子节点
        cur_node = self.__class_course_list[user_msg[0]]
        course_score_0 = cur_node.content
        cur_node = cur_node.next[user_msg[1]]
        course_score_1 = cur_node.content
        cur_node = cur_node.next[user_msg[2]]
        course_score_2 = cur_node.content
        # 获取课程分数
        result = []
        for iid in candidate_list:
            if iid in course_score_2:
                result.append((iid, course_score_2[iid]))
                continue
            if iid in course_score_1:
                result.append((iid, course_score_1[iid]))
                continue
            result.append((iid, course_score_0[iid]))
        result = heapq.nlargest(RECOMMEND_OPEN_COURSE_NUM, result, key=lambda k: k[1])
        return result


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
        for uid, projectid, activiesid, course_package_id, candidate_list in user_course:
            score = [(iid, self.__course_score.get(iid, 2.5)) for iid in candidate_list]
            score = heapq.nlargest(RECOMMEND_COURSE_NUM, score, key=lambda k: k[1])
            result.append((uid, projectid, activiesid, course_package_id, score))
        return result


