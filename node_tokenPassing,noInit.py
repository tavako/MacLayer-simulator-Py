import queue
from log_event import log_event
from tracked_message import tracked_message
class Node:
    def __init__(self , uid ):
        self.status = "idle"
        self.uid = uid
        self.transmit_history = []
        self.transmit_buffer = queue.Queue()
        self.max_retry_before_timeout = 3
        self.initial_backoff_period = 2 #unit slots 
        self.bits_per_slot = 40
        self.mac_scheme = "default"
        self.recieved_packets = []
        self.token_owner = 1
        self.isAP = False
        self.has_token = False
    def set_coordinate(self , x , y , range):
        #range can be calculated with emitted power later on
        self.x = x
        self.y = y
        self.range = range
        return
    
    def recieve(self,message , tick_counter):
        self.recieved_packets.append(log_event(message , tick_counter))
        if message.startswith("control"):
            whosturn = int(message[17:])
            if whosturn == self.uid :
                self.has_token = True
            else :
                self.has_token = False


    def print_packets(self):
        for packet in self.recieved_packets:
            packet.print_logs()

    def queue_message(self , message , current_time):
        #to make whole system event based we need to make an event every time a message is queued or stays in queue after failing to win the contention window
        self.transmit_buffer.put(tracked_message(message , current_time))
        
    def get_uid(self):
        return self.uid
    def transmit_message(self , current_time):
        message = self.transmit_buffer.get()
        message.set_delay_to_deliver(current_time)
        if not self.transmit_buffer.empty():
            self.transmit_buffer.queue[0].set_wait_in_queue(current_time)
        self.transmit_history.append(message)
        return message.message 

    def is_ready_transmit(self):
        return (not self.transmit_buffer.empty()) and (self.has_token or self.isAP)

#access point functions
    def send_beacon(self , current_time):
        self.transmit_buffer.put(tracked_message("control " + "token for" + str(self.token_owner) , current_time))
        self.isAP = True
        self.token_owner += 1
        if self.token_owner == 3 :# we need virtual ids or a map to change it
            self.token_owner = 1
        
    