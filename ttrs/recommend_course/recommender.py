from .data_center import *
from .model import *
from ..utils.process_shower import ProcessShower
from ..settings.rs_course_setting import *


class CourseRecommender:
    def __init__(self):
        return

    def run(self):
        # 初始化组件
        data_manager = CourseDataManager()
        process_shower = ProcessShower('课程推荐系统', VERBOSE)
        process_shower.show_start()

        # 训练预测模型
        model = UserCourseSVD()
        train_data = data_manager.get_user_course_score()
        process_shower.show_start_subprocess('训练预测模型')
        model.fit(train_data)
        process_shower.show_end_subprocess()

        # 预测普通用户选修课评分
        process_shower.show_start_subprocess('预测普通用户选修课评分')
        elective_course_pre_data = data_manager.get_elective_course_pre_data()
        elective_course_result = model.predict(elective_course_pre_data, pre_type='normal', rec_n=RECOMMEND_COURSE_NUM)
        process_shower.show_end_subprocess()

        # 预测冷启动用户选修课评分
        process_shower.show_start_subprocess('预测冷启动用户选修课评分')
        elective_cold_model = UserElectiveCourseCold()
        elective_cold_model.fit(train_data)
        cold_elective_course_pre_data = data_manager.get_cold_elective_course_pre_data()
        cold_elective_course_result = elective_cold_model.predict(cold_elective_course_pre_data)
        process_shower.show_end_subprocess()

        # 保存选修课推荐结果
        process_shower.show_start_subprocess('保存选修课推荐结果')
        data_manager.save_to_db(elective_course_result+cold_elective_course_result, data_type='elective_course_data')
        del elective_course_result, cold_elective_course_result, cold_elective_course_pre_data
        process_shower.show_end_subprocess()

        # 预测普通用户开放课程评分
        process_shower.show_start_subprocess('预测普通用户开放课程评分')
        user_open_course_list = data_manager.get_open_course_pre_data()
        open_course_result = model.predict(user_open_course_list, rec_n=RECOMMEND_OPEN_COURSE_NUM)
        process_shower.show_end_subprocess()

        # 预测冷启动用户开放课程评分
        process_shower.show_start_subprocess('预测冷启动用户开放课程评分')
        open_cold_model = UserOpenCourseCold()
        train_info = data_manager.get_user_info()
        open_cold_model.fit(train_data, train_info)
        cold_open_course_pre_data = data_manager.get_cold_open_course_pre_data()
        cold_open_course_result = open_cold_model.predict(cold_open_course_pre_data)
        process_shower.show_end_subprocess()

        # 保存开放课推荐结果
        process_shower.show_start_subprocess('保存开放课推荐结果')
        data_manager.save_to_db(open_course_result + cold_open_course_result, data_type='open_course_data')
        process_shower.show_end_subprocess()

        process_shower.show_end()
        return

