from ttrs.course_recommender_system.recommender import *
import time

start = time.time()
recommender = CourseRecommender()
recommender.run()
print('推荐系统运行完毕，总用时', int((time.time() - start) // 60), '分', int((time.time() - start) % 60), '秒')

