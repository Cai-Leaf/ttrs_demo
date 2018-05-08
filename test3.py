from ttrs.utils import db_data
from datetime import datetime, timedelta


close_project = db_data.read_db_to_df(sql="SELECT DISTINCT projectid, close_date FROM ts501",
                                      contain=['projectid', 'close_date'],
                                      info='test', verbose=True)
now = datetime.now()
result = set()
for pid, date in close_project.itertuples(index=False):
    if now + timedelta(days=7) > date.to_pydatetime():
        result.add(pid)
print(result)







