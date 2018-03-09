import time


class ProcessShower:
    def __init__(self, presess_name, verbose=True):
        self.presess_name = presess_name
        self.prosess_start_time = None
        self.sub_process_name = None
        self.sub_process_start_time = None
        self.main_length = 60
        self.sub_length = 40
        self.verbose = verbose

    def show_start(self):
        if self.verbose:
            self.prosess_start_time = time.time()
            print(self.presess_name+' 开始运行 '+'—'*(self.main_length-len(' 开始运行 '+self.presess_name)))
        return

    def show_end(self):
        if self.verbose:
            print('—'*(self.main_length-1))
            print(self.presess_name, '运行结束，用时',
                  int((time.time() - self.prosess_start_time) // 60), '分',
                  int((time.time() - self.prosess_start_time) % 60), '秒')
        return

    def show_start_subprocess(self, presess_name):
        if self.verbose:
            self.sub_process_name = presess_name
            self.sub_process_start_time = time.time()
            print(self.sub_process_name+' 开始 '+'—'*(self.sub_length-len(' 开始 '+self.sub_process_name)))
        return

    def show_end_subprocess(self):
        if self.verbose:
            print(self.sub_process_name, '结束，用时',
                  int((time.time() - self.sub_process_start_time) // 60), '分',
                  int((time.time() - self.sub_process_start_time) % 60), '秒')
        return

