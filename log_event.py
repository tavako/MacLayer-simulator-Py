class log_event:
    def __init__(self , message , time_stamp):
        self.message = message
        self.time_stamp = time_stamp

    def print_logs(self):
        print("t:"+str(self.time_stamp)+","+self.message)