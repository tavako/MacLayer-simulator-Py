import queue
import random
from log_event import log_event
from tracked_message import tracked_message
from pair import pair
from sch_task import sch_task 
class Node:
    base_ack_wait = 2
    backoff_exponent = 2
    max_retry_before_timeout = 3
    max_retry_cw = 3
    base_contention_windows = 2
    def __init__(self , uid ):
        self.status = "idle"
        self.uid = uid
        self.transmit_history = []
        self.transmit_buffer = []
        self.initial_backoff_period = random.randint(1,3) #unit slots 
        self.bits_per_slot = 40
        self.mac_scheme = "duallink_LBS"
        self.recieved_packets = []
        self.isAP = False
        self.initialization = True
        self.beacon_order = 100
        self.maxPanId = 1
        self.panMap = []
        self.panId = -1
        self.is_wait_msg_ack =False
        self.is_wait_msg_cw = False
        self.current_cw = 0
        self.cw_resets = 0
        self.current_retry = 0
        self.is_wait_ack = False
        self.current_backoff = self.initial_backoff_period
        self.wait_ack = Node.base_ack_wait
        self.timeslots = [None]*20    #18 5-length timeslots and 2 timeslots for rejoin 
        self.timeslots[0] = 0
        self.timeslots[1] = 0
        self.occupied_timeslots = 1
        self.start_rejoin = -10
        self.events = []
        self.can_transmit = False
        self.current_initialize_request = ""
    
    def set_coordinate(self , x , y , range):
        #range can be calculated with emitted power later on
        self.x = x
        self.y = y
        self.range = range
        return
    
    def recieve(self,message , tick_counter):
        self.recieved_packets.append(log_event(message , tick_counter))
        if message.startswith("control"):
            if message.startswith("control " + "initialize,beaconMac:"):
                self.regiser_BS(message , tick_counter )
                #remember the request and retries when model of channels is more complete
            if message.startswith("control request_join,beaconMac:") and self.isAP:
                clientMac = message[message.find("myMac:")+6:]
                clientpanId = self.maxPanId
                if self.uid == int(message[message.find(":")+1:message.find("myMac")]):
                    self.transmit_buffer.append(tracked_message("control accept_join,beaconMac:" + str(self.uid) + "clientMac:" + str(clientMac) + "clientPanid:" + str(clientpanId) , tick_counter ,1 ))
                self.maxPanId+=1
            if message.startswith("control accept_join,beaconMac:"):
                clientMac_rec = message[message.find("clientMac:")+len("clientMac:") : message.find("clientPanid:")]
                if int(clientMac_rec) == self.uid :
                    self.is_wait_ack = False
                    self.current_backoff = self.initial_backoff_period
                    self.panId = int(message[message.find("clientPanid:")+len("clientPanid:"):])
            if message.startswith("control "+"joinOpportunity,beaconMac:"):
                if self.panId == -1:
                    self.regiser_BS(message , tick_counter )
        elif self.isAP:
            target_pid = message.split(":")[0]
            self.transmit_buffer.append(tracked_message("ack" + target_pid , tick_counter , 1))
        elif message.startswith("ack"):
            target_pid = message[message.find("ack")+len("ack"):]
            if self.uid == int(target_pid):
                self.is_wait_msg_ack = False
                self.current_backoff =self.initial_backoff_period

    
                    
    def regiser_BS(self , message , tick_counter):
        self.current_initialize_request = "control request_join,beaconMac:" + message.split(":")[1] + "myMac:" + str(self.uid) 
        self.events.append(sch_task(tick_counter + self.current_backoff , "queue_message" , [self.uid , self.current_initialize_request]))
        self.is_wait_ack = True
        self.wait_ack = Node.base_ack_wait+self.current_backoff
        self.current_backoff = self.current_backoff*Node.backoff_exponent
        self.events.append(sch_task(tick_counter+self.wait_ack , "check_ack" , [self.uid , self.wait_ack ]))
        self.permit_transmit(tick_counter , 35)

    def continuos_LBS(self , current_time , target_medium):
        self.events.append(sch_task(current_time , "check_medium_status" , [self.uid , target_medium ]))

    def set_current_cw(self , cw , current_time , target_medium):
        self.current_cw =  cw
        if cw == Node.base_contention_windows:
            self.is_wait_msg_cw = False
            self.current_cw = 0
            self.permit_transmit(current_time , 5 )
        else:
            self.events.append(sch_task(current_time+1 , "LBS" , [self.uid , target_medium]))
    
    def reset_cw(self , current_time , target_medium):
        if self.cw_resets < Node.max_retry_cw:
            self.current_cw = 0
            self.events.append(sch_task(current_time+1 , "LBS" , [self.uid , target_medium]))
            self.cw_resets += 1
        else:
            self.is_wait_msg_cw = False
            self.current_cw = 0
            self.transmit_history.append(tracked_message("timeout on acquire channel" , current_time , 0))
        

    def check_ack_initialize(self , tick_counter):
        if self.is_wait_ack :
            if self.current_retry < Node.max_retry_before_timeout:
                self.current_retry += 1
                self.events.append(sch_task(tick_counter + self.current_backoff , "queue_message" , [self.uid ,self.current_initialize_request  ]))
                self.is_wait_ack = True
                self.wait_ack = self.base_ack_wait+self.current_backoff
                self.current_backoff = self.current_backoff*Node.backoff_exponent
                self.events.append(sch_task(tick_counter+self.wait_ack , "check_ack" , [self.uid , self.wait_ack ]))
            else:
                # request timeout
                self.transmit_history.append(tracked_message("timeout" + self.current_initialize_request , tick_counter - self.current_backoff/Node.backoff_exponent , 0))
        else:
            self.current_retry = 0 
        return
    
    def check_ack_msg(self , tick_counter):
        if self.is_wait_msg_ack:
            if self.msg_ack_counter < Node.max_retry_before_timeout:
                self.msg_ack_counter +=1
                self.events.append(sch_task(tick_counter + self.current_backoff , "queue_message" , [self.uid  , self.last_msg]))
                self.is_wait_msg_ack = True
                self.wait_msg_ack = self.current_backoff + Node.base_ack_wait
                self.current_backoff = self.current_backoff*Node.backoff_exponent
                self.events.append(sch_task(tick_counter+ self.wait_msg_ack , "check_msg_ack" , [self.uid , self.last_msg]))
            else:
                self.transmit_history.append(tracked_message("timeout" + self.last_msg , tick_counter - self.current_backoff/Node.backoff_exponent , 0))
                self.reset_msg_ack()
                if self.transmit_buffer != []:
                    self.continuos_LBS(tick_counter , 0 )
        else:
            self.reset_msg_ack()
    def reset_msg_ack(self):
        self.msg_ack_counter = 0
        self.is_wait_msg_ack = False 
    
    def permit_transmit(self ,current_time , duration):
        self.can_transmit = True
        self.events.append(sch_task(current_time+duration , "remove_transmit_permit" , [self.uid]))

    def remove_permit(self):
        self.can_transmit = False

        
    def print_packets(self):
        for packet in self.recieved_packets:
            packet.print_logs()

    def queue_message(self , message , current_time , medium = 0):
        #to make whole system event based we need to make an event every time a message is queued or stays in queue after failing to win the contention window
        self.transmit_buffer.append(tracked_message(message , current_time , medium))
        if not (self.is_wait_msg_cw or self.is_wait_msg_ack) and medium == 0: 
            self.continuos_LBS(current_time  , 0)
            self.is_wait_msg_cw = True
        
    def get_uid(self):
        return self.uid
    
    def transmit_message(self , current_time , medium_asking):
        first_instance = True
        msg_to_be_sent = None
        for i in range(len(self.transmit_buffer)):
            msg = self.transmit_buffer[i]
            if msg.target_medium == medium_asking :
                if first_instance:
                    msg.set_delay_to_deliver(current_time)
                    self.transmit_history.append(msg)
                    if not msg.message.startswith("control"):
                        msg.message = str(self.uid)+":"+msg.message
                    msg_to_be_sent = msg
                    self.last_msg = msg
                    first_instance = False
                    if not self.isAP:
                        self.wait_msg_ack = True
                        self.msg_ack_counter = 0
                        self.events.append(sch_task(current_time+Node.base_ack_wait , "check_msg_ack" , [self.uid , self.last_msg]))
                    del(self.transmit_buffer[i])
                else:
                    msg.set_wait_in_queue(current_time)
                    break
        return msg_to_be_sent.message

    def is_ready_transmit(self , medium_asking ):
        if (not self.transmit_buffer == []) and (self.can_transmit or self.isAP):
            for msg in self.transmit_buffer:
                if msg.target_medium == medium_asking:
                    return True
        return False
                

#access point functions
    def send_beacon(self , current_time):
        if(current_time%self.beacon_order ==  0):
            if self.initialization:
                self.transmit_buffer.append(tracked_message("control " + "initialize,beaconMac:" + str(self.uid) , current_time , 1))
                self.start_initialization_point = current_time
                self.initialization  = False
                #40 time slots for initialization need a new event on scheduler
            else:
                self.transmit_buffer.append(tracked_message("control "+"joinOpportunity,beaconMac:" + str(self.uid) , current_time , 1 ))
                self.start_rejoin = current_time
                #10 time slots for rejoin