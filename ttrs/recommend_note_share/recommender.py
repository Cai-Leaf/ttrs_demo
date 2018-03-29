from .model import *
from ..utils.process_shower import ProcessShower
from .data_center import *


class NoteShareRecommender:
    def __init__(self):
        return

    def run(self):
        # 初始化组件
        data_manager = NoteShareDataManager()
        process_shower = ProcessShower('研修日志推荐系统', True)
        process_shower.show_start()

        # 训练预测模型
        process_shower.show_start_subprocess('训练预测模型')
        model = ContentSimilarityModel()
        pre_data = data_manager.load_content_train_data()
        model.fit(pre_data)
        process_shower.show_end_subprocess()

        # 预测普通用户研修日志评分
        process_shower.show_start_subprocess('预测普通用户研修日志评分')
        pre_data = data_manager.get_pre_data()
        item_score = data_manager.get_item_score()
        pre_result = model.predict(pre_data, item_score)
        process_shower.show_end_subprocess()

        # 训练冷启动模型
        process_shower.show_start_subprocess('训练冷启动模型')
        cold_model = NoteShareColdModel()
        cold_model.fit(item_score)
        process_shower.show_end_subprocess()

        # 预测冷启动用户研修日志评分
        process_shower.show_start_subprocess('预测冷启动用户研修日志评分')
        cold_pre_data = data_manager.get_cold_pre_data()
        cold_pre_result = cold_model.predict(cold_pre_data)
        process_shower.show_end_subprocess()

        # 保存预测结果
        process_shower.show_start_subprocess('保存预测结果')
        data_manager.save_to_db(pre_result + cold_pre_result)
        process_shower.show_end_subprocess()

        process_shower.show_end()
        return

