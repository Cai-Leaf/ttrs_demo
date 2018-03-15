import datetime
from collections import defaultdict
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
import random

a = 30
now_time = datetime.datetime.now()
yes_time = now_time + datetime.timedelta(days=-a)
print('"' + yes_time.strftime('%Y-%m-%d') + '"')
