import heapq
import random
from collections import defaultdict
from ..settings.rs_study_activity_setting import RECOMMEND_NUM


class PopRecommendModel:
    def __init__(self):
        self.item_score = defaultdict(int)
        return

    def fit(self, user_activity_data):
        for _, pid, iid in user_activity_data.itertuples(index=False):
            self.item_score[iid] += 1
        return

    def predict(self, data):
        result = []
        for uid, pid, ssc, sc, item_list, new_item_list in data:
            pre_item = heapq.nlargest(RECOMMEND_NUM, [(iid, self.item_score[iid]) for iid in item_list], key=lambda k: k[1])
            pre_item = [item[0] for item in pre_item]
            pre_len = len(pre_item)
            # 在预测结果中插入新物品
            for new_item in new_item_list:
                index = random.randint(pre_len//3, pre_len//3*2)
                pre_item.insert(index, new_item)
            result.append((uid, pid, ssc, sc, pre_item))
        return result


