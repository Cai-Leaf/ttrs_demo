from .model import *
from ..utils.process_shower import ProcessShower
from ..settings.rs_note_share_setting import VERBOSE
from .data_center import *


class NoteShareRecommender:
    def __init__(self):
        return

    def run(self):
        # 初始化组件
        data_manager = NoteShareDataManager()
        process_shower = ProcessShower('研修日志推荐系统', VERBOSE)
        process_shower.show_start()

        # 训练内容相似度模型
        process_shower.show_start_subprocess('训练内容相似度模型')
        content_model = ContentSimilarityModel()
        content_pre_data = data_manager.load_content_train_data()
        content_model.fit(content_pre_data)
        del content_pre_data
        process_shower.show_end_subprocess()

        # 训练协同过滤模型
        process_shower.show_start_subprocess('训练协同过滤模型')
        cf_model = NoteCollaborativeFiltering()
        cf_pre_data = data_manager.get_user_item()
        cf_model.fit(cf_pre_data)
        del cf_pre_data
        process_shower.show_end_subprocess()

        # 预测普通用户研修日志评分
        process_shower.show_start_subprocess('预测普通用户研修日志评分')
        pre_data = data_manager.get_pre_data()
        item_score = data_manager.get_item_score()
        pre_result = mix_predict(content_model, cf_model, pre_data, item_score)
        del pre_data, item_score
        process_shower.show_end_subprocess()

        # 训练冷启动模型
        process_shower.show_start_subprocess('训练冷启动模型')
        cold_model = NoteShareColdModel()
        item_projectid_score = data_manager.get_item_projectid_score()
        cold_model.fit(item_projectid_score)
        del item_projectid_score
        process_shower.show_end_subprocess()

        # 预测冷启动用户研修日志评分
        process_shower.show_start_subprocess('预测冷启动用户研修日志评分')
        cold_pre_data = data_manager.get_cold_pre_data()
        cold_pre_result = cold_model.predict(cold_pre_data)
        del cold_pre_data
        process_shower.show_end_subprocess()

        # 保存预测结果
        process_shower.show_start_subprocess('保存预测结果')
        data_manager.save_to_db(pre_result + cold_pre_result)
        process_shower.show_end_subprocess()

        process_shower.show_end()
        return

