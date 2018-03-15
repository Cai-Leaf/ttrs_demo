import heapq
import random
from collections import defaultdict


class PopRecommendModel:
    def __init__(self):
        self.class_score = defaultdict(lambda: defaultdict(int))
        return

    def fit(self, user_activity_data):
        for _, sc, ssc, iid in user_activity_data:
            self.class_score[sc+'-'+ssc][iid] += 1

        return

    def predict(self, data):
        result = []
        for uid, pid, sc, ssc, item_list, new_item_list in data:
            item_score = self.class_score[sc+'-'+ssc]
            pre_item = heapq.nlargest(10, [(iid, item_score[iid]) for iid in item_list], key=lambda k: k[1])
            pre_item = [item[0] for item in pre_item]
            pre_len = len(pre_item)
            for new_item in new_item_list:
                index = random.randint(pre_len//3, pre_len//3*2)
                pre_item.insert(index, new_item)
            result.append((uid, pid, pre_item))
        return result


