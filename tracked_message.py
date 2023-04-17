class tracked_message:
    def __init__(self,message,s_time):
        self.message = message 
        self.start_time  = s_time
        self.wait_in_queue = 0
    def set_wait_in_queue(self  , current_time):
        self.wait_in_queue = current_time - self.start_time
    def set_delay_to_deliver(self , current_time):
        self.delay_to_deliver = current_time  - self.start_time

    