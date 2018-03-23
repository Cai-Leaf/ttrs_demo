from ..utils.process_shower import *
from .data_center import *
from .model import *


class ResourceShareRecommender:
    def __init__(self):
        return

    def run(self):
        # 初始化组件
        data_manager = ResourceShareDataManager()
        process_shower = ProcessShower('资源推荐系统', True)
        process_shower.show_start()

        # 训练类别预测模型
        process_shower.show_start_subprocess('训练类别预测模型')
        class_resource_modle = ClassRecommendModel()
        item_msg_data = data_manager.get_item_msg_data()
        class_resource_modle.fit(item_msg_data)
        process_shower.show_end_subprocess()

        # 训练协同过滤预测模型
        process_shower.show_start_subprocess('训练协同过滤预测模型')
        item_cold_modle = ItemCollaborativeFiltering()
        user_item = data_manager.get_user_item()
        item_cold_modle.fit(user_item)
        process_shower.show_end_subprocess()

        # 预测普通用户推荐资源
        process_shower.show_start_subprocess('预测普通用户推荐资源')
        pre_data = data_manager.get_pre_data()
        pre_result = mix_predict(class_model=class_resource_modle, item_model=item_cold_modle, pre_data=pre_data)
        process_shower.show_end_subprocess()

        # 训练冷启动用户预测模型
        process_shower.show_start_subprocess('训练冷启动用户预测模型')
        resource_share_cold_model = ResourceShareColdModel()
        user_info = data_manager.get_user_info()
        resource_share_cold_model.fit(user_item, user_info)
        process_shower.show_end_subprocess()

        # 预测冷启动用户推荐资源
        process_shower.show_start_subprocess('预测冷启动用户推荐资源')
        cold_elective_course_pre_data = data_manager.get_cold_pre_data()
        cold_pre_result = resource_share_cold_model.predict(cold_elective_course_pre_data)
        process_shower.show_end_subprocess()

        # 保存推荐结果
        process_shower.show_start_subprocess('保存推荐结果')
        data_manager.save_to_db(pre_result+cold_pre_result)
        process_shower.show_end_subprocess()

        process_shower.show_end()
        return

