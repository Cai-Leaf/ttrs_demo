from ttrs.utils import db_data
from datetime import datetime, timedelta


data = db_data.read_db_to_df(sql="""SELECT blogid, projectid, pl_count, ll_count, dz_count, star, DATEDIFF("2018-05-18", createtime) as createtime
                                             FROM ts505
                                             WHERE projectid IN (SELECT DISTINCT projectid FROM ts501)""",
                                      contain=['blogid', 'projectid', 'pl_count', 'll_count', 'dz_count', 'star', 'createtime'],
                                      info='test', verbose=True)


def calc_score(group):
    pl_count = min(10, group['pl_count'].sum())
    dz_count = min(10, group['dz_count'].sum())
    ll_count = min(10, group['ll_count'].sum())
    star = min(5, group['star'].mean())
    createtime = max(30, group['createtime'].mean())
    score = 0.1*pl_count/10+0.1*ll_count/10+0.1*dz_count/10+0.4*star/5+0.3*30/createtime
    return score

data = data.groupby(['projectid', 'blogid']).apply(calc_score).to_frame('score').reset_index()
print(data)






