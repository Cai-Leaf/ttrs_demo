"""
Mysql 数据库的配置文件
"""

# 读数据时的数据库配置
# Mysql数据库地址
R_HOST = 'localhost'
# Mysql用户名
R_USER = 'root'
# Mysql密码
R_PASSWORD = '123456'
# Mysql数据库名
R_DATABASE = 'tt_nov'
# 字符编码
R_CHARSET = 'utf8'

# 写数据时的数据库配置
# Mysql数据库地址
W_HOST = 'localhost'
# Mysql用户名
W_USER = 'root'
# Mysql密码
W_PASSWORD = '123456'
# Mysql数据库名
W_DATABASE = 'tt_result'
# 字符编码
W_CHARSET = 'utf8'
# 存入数据库时，数据分区大小
MAX_SAVE_DATA_BACH_SIZE = 1024*16
