from ttrs.recommend_course.recommender import *
from ttrs.recommend_info_tech.recommender import *
from ttrs.recommend_study_activity.recommender import *
from ttrs.recommend_resource_share.recommender import *

# 运行课程推荐系统
# recommender = CourseRecommender()
# recommender.run()

# 运行信息技术技巧大全推荐系统
# recommender = InfoTechRecommender()
# recommender.run()

# 运行研修活动推荐系统
# recommender = StudyActivityRecommender()
# recommender.run()

# 运行资源推荐系统
recommender = ResourceShareRecommender()
recommender.run()





