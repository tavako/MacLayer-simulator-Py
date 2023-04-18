import random
import math 
class Medium:
#need support for fading , shadowing , noise addition , and multiple channels 
    def __init__(self , load_per_tick , m_type):
        self.load_per_tick = load_per_tick
        self.m_type = m_type
        self.failure_probability = 1e-8
        self.channel_type = "no failure"
        self.subscribers = []
        self.collisions = []
        self.is_busy = False

    def add_batch_subscriber(self , susbcribers):
        self.subscribers = self.subscribers + susbcribers
    def add_subscriber(self, node):
        self.subscribers.append(node)
    
    @staticmethod
    def calc_dis(x1 , y1 , x2 , y2):
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)

    def transmit_message_range_limited(self , message , initial , tick_counter):
        state, new_message  = self.check_channel_imperfection(message)
        if state == "success":
            for subscriber in self.subscribers :
                if(subscriber != initial and Medium.calc_dis(initial.x , initial.y , subscriber.x , subscriber.y ) < initial.range ):
                    subscriber.recieve(new_message , tick_counter)
        return 
    
    def transmit_message_graph_connected(self , message , initial , tick_counter):
        state, new_message  = self.check_channel_imperfection(message)
        if state == "success":
            for subscriber in initial.connections :
                subscriber.recieve(new_message , tick_counter)
        return 
    
    def transmit_message_directly(self , message , initial , tick_counter):
        #pass None as inital for outside broadcast interference
        #in case of simple failure ignores message if failed 
        state, new_message  = self.check_channel_imperfection(message)
        if state == "success":    
            for subscriber in self.subscribers :
                if(subscriber != initial):
                    subscriber.recieve(new_message , tick_counter)

    def check_channel_imperfection(self , message):
        if self.channel_type == "simple random failure":
            if random.random() < self.failure_probability:
                state = "failed"
                new_message = ""
            else:
                state = "success"
                new_message = message
        else:
            state = "success"
            new_message = message 
        return state , new_message
    
    def resolve_requests(self , tick_counter):
        self.is_busy = False
        nodes_transmitted = []
        for subscriber in self.subscribers:
            if subscriber.is_ready_transmit():
                if not self.is_busy :
                    self.is_busy = True
                    self.transmit_message_directly(subscriber.transmit_message(tick_counter) , subscriber , tick_counter)
                    nodes_transmitted.append(subscriber.get_uid())
                else:
                    self.collisions.append([subscriber.get_uid(),subscriber.transmit_message(tick_counter)])
                    nodes_transmitted.append(subscriber.get_uid())
        return nodes_transmitted
    
    def pending_transmission(self):
        for susbscriber in self.subscribers:
            if susbscriber.is_ready_transmit():
                return True
        return False