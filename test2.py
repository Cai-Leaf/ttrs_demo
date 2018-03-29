import numpy as np
# import jieba
# import re
#
# content2 = """<p>信息技术的使用不在乎要多么高的技术含量，它的真正意义在于能够很好的辅助教学，他只是教学手段中的一种手段，
# 在过去我的理解就是要求多么高的技术含量，多么花哨的图片或者PPT，只有这样就算是会运用信息技术了，
# 学习之后我了解到每一种技术都是一种很好的开启方式，每一种技术的运用都需要了解其根本，再经过长年累月的坚持探究才能真正掌握它运用它驾驭它。</p>"""
#
# flag_word = r"[\s+\.\!\/_,$?%^*()<>+\"\';:1234567890]+|[——！，。？、~@#￥%……&*（）《》；【】“”：:]+"
# html_word = r'<[^>]+>'
# stop_word = {'quot', ' ', 'nbsp'}
# flag_dr = re.compile(flag_word)
# html_dr = re.compile(html_word)
#
# dd = html_dr.sub(' ', content2)
# dd = flag_dr.sub(' ', dd)
#
# # print(dd)
# seg_list = jieba.cut(dd)
# #
# print(" ".join([word for word in seg_list if word not in stop_word and len(word) > 1]))


