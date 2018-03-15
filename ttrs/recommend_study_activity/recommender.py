from ..utils.process_shower import *
from .data_center import *
from .model import *


class StudyActivityRecommender:
    def __init__(self):
        return

    def run(self):
        # 初始化组件
        data_manager = StudyActivityDataManager()
        process_shower = ProcessShower('研修活动推荐系统', True)
        process_shower.show_start()

        # 训练预测模型
        model = PopRecommendModel()
        user_activity_data = data_manager.get_user_activity_data()
        process_shower.show_start_subprocess('训练预测模型')
        model.fit(user_activity_data)
        process_shower.show_end_subprocess()

        process_shower.show_end()
        return

