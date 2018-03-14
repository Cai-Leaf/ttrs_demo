from ..utils.process_shower import ProcessShower
from .data_center import InfoTechDataManager
from .model import *
from ..settings.rs_info_tech_setting import VERBOSE


class InfoTechRecommender:
    def __init__(self):
        return

    def run(self):
        # 初始化组件
        data_manager = InfoTechDataManager()
        process_shower = ProcessShower('信息技术技巧大全推荐系统', VERBOSE)
        process_shower.show_start()

        # 训练预测模型
        process_shower.show_start_subprocess('训练预测模型')
        model = MixedCollaborativeFiltering()
        user_item_data = data_manager.get_user_item_data()
        item_msg_data = data_manager.get_item_msg_data()
        model.fit(user_item_data, item_msg_data)
        process_shower.show_end_subprocess()
        del item_msg_data

        # 预测普通用户信息技术技巧大全评分
        process_shower.show_start_subprocess('预测普通用户用户信息技术技巧大全评分')
        pre_data = data_manager.get_pre_data()
        item_score = data_manager.get_item_score()
        pre_result = model.predict(pre_data, item_score)
        process_shower.show_end_subprocess()

        # 训练冷启动用户预测模型
        process_shower.show_start_subprocess('训练冷启动用户预测模型')
        cold_model = InfoTechColdModel()
        user_info = data_manager.get_user_info()
        cold_train_data = data_manager.get_cold_train_data()
        cold_model.fit(cold_train_data, user_info)
        process_shower.show_end_subprocess()

        # 预测冷启动用户信息技术技巧大全评分
        process_shower.show_start_subprocess('预测冷启动用户信息技术技巧大全评分')
        cold_pre_data = data_manager.get_cold_pre_data()
        cold_pre_result = cold_model.predict(cold_pre_data)
        process_shower.show_end_subprocess()

        # 保存预测结果
        process_shower.show_start_subprocess('保存预测结果')
        data_manager.save_to_db(pre_result + cold_pre_result)
        process_shower.show_end_subprocess()

        process_shower.show_end()
        return

