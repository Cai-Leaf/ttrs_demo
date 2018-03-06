from .data_center import *
from .model import *
import time


class CourseRecommender:
    def __init__(self):
        return

    def run(self):
        # 读入训练数据
        data_manager = CourseDataManager()

        # 训练预测模型
        model = UserCourseSVD()
        train_data = data_manager.get_user_course_score()
        start = time.time()
        print('开始训练模型')
        model.fit(train_data)
        print('模型训练完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')

        # 获取普通选修课候选列表
        start = time.time()
        print('预测普通用户选修课评分')
        elective_course_pre_data = data_manager.get_elective_course_pre_data()
        # 预测普通用户选修课评分
        elective_course_result = model.predict(elective_course_pre_data, pre_type='normal')
        print('预测完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')

        # 训练选修课冷启动模型
        start = time.time()
        print('预测冷启动用户选修课评分')
        elective_cold_model = UserElectiveCourseCold()
        elective_cold_model.fit(train_data)
        # 获取冷启动用户选修课候选列表
        cold_elective_course_pre_data = data_manager.get_cold_elective_course_pre_data()
        # 预测冷启动用户选修课评分
        cold_elective_course_result = elective_cold_model.predict(cold_elective_course_pre_data)
        print('预测完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')
        # 保存预测结果
        data_manager.save_to_db(elective_course_result+cold_elective_course_result, data_type='elective_course_data')
        del elective_course_result, cold_elective_course_result

        # 获取普通用户开放课程候选列表
        user_open_course_list = data_manager.get_open_course_pre_data()
        start = time.time()
        print('预测普通用户开放课程评分')
        # 预测普通用户开放课程评分
        open_course_result = model.predict(user_open_course_list)
        print('预测完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')

        # 训练开放课程冷启动模型
        start = time.time()
        print('预测冷启动用户开放课程评分')
        open_cold_model = UserOpenCourseCold()
        train_info = data_manager.get_user_info()
        open_cold_model.fit(train_data, train_info)
        # 获取冷启动用户推荐列表
        cold_open_course_pre_data = data_manager.get_cold_open_course_pre_data()
        # 预测冷启动用户开放课程评分
        cold_open_course_result = open_cold_model.predict(cold_open_course_pre_data)
        print('预测完毕，用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')
        # 保存预测结果
        data_manager.save_to_db(open_course_result + cold_open_course_result, data_type='elective_course_data')
        del open_course_result, cold_open_course_result
        return

