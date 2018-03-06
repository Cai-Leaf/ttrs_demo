import pandas as pd


def read_csv_to_df(filename, contain=None):
    try:
        data = pd.read_csv(filename, header=0, usecols=contain, encoding='utf-8')
    except IOError:
        raise IOError(filename+' 打开文件失败')
    except ValueError:
        raise ValueError(filename+' 打开文件失败，文件未包含指定参数')
    if len(data) == 0:
        raise ValueError(filename+' 打开文件失败，无法读入空文件')
    print(filename+' 文件读取成功')
    return data


def make_df_to_csv(filename, data, contain=None, info=""):
    try:
        data = pd.DataFrame(data, columns=contain)
        data.to_csv(filename, index=False)
    except IOError:
        raise IOError(filename+' 创建文件失败')
    except ValueError:
        raise ValueError(filename+' 创建文件失败，参数错误')
    print(info+'文件已保存到 '+filename)
    return
