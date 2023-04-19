import random
from log_event import log_event
from tracked_message import tracked_message
from pair import pair
from sch_task import sch_task 
class Node:
    base_ack_wait = 2
    backoff_exponent = 2
    max_retry_before_timeout = 3
    def __init__(self , uid ):
        self.status = "idle"
        self.uid = uid
        self.transmit_history = []
        self.transmit_buffer = []
        self.initial_backoff_period = random.randint(1,3) #unit slots 
        self.bits_per_slot = 40
        self.mac_scheme = "tdma-fixed-DualLink"
        self.recieved_packets = []
        self.isAP = False
        self.initialization = True
        self.beacon_order = 100
        self.maxPanId = 1
        self.panMap = []
        self.panId = -1
        self.current_retry = 0
        self.is_wait_ack = False
        self.current_backoff = self.initial_backoff_period
        self.wait_ack = Node.base_ack_wait
        self.timeslots = [None]*20    #18 5-length timeslots and 2 timeslots for rejoin 
        self.timeslots[0] = 0
        self.timeslots[1] = 1
        self.timeslots[2] = 2
        self.occupied_timeslots = 1
        self.start_rejoin = -10
        self.events = []
        self.can_transmit = False
        self.current_initialize_request = ""
        self.timeslotOwner = 0
    
    def set_coordinate(self , x , y , range):
        #range can be calculated with emitted power later on
        self.x = x
        self.y = y
        self.range = range
        return
    
    def recieve(self,message , tick_counter):
        self.recieved_packets.append(log_event(message , tick_counter))
        if message.startswith("control"):
             #check tdma schedule and plan accordingly
            if message.startswith("control " + "beaconMac:"):
                self.APMAC = message.split(":")[1][0:message.find("tdma-sch:")] 
                self.timeslots = message.split(":")[2].split(",")
                self.sch_for_transmit(tick_counter)
    
    def sch_for_transmit(self , tick_counter):
        for i in range(len(self.timeslots)):
            timeslot = self.timeslots[i]
            if timeslot != "None":
                if int(timeslot) == self.uid:
                    self.events.append(sch_task(tick_counter + (i)*5 + 1  , "grant_transmit_permit" , [self.uid]))
                    return
        return 
    
    def permit_transmit(self ,current_time , duration):
        self.can_transmit = True
        self.events.append(sch_task(current_time+duration , "remove_transmit_permit" , [self.uid]))

    def remove_permit(self):
        self.can_transmit = False

        
    def print_packets(self):
        for packet in self.recieved_packets:
            packet.print_logs()

    def queue_message(self , message , current_time , target = -1 ,  medium = 0):
        #to make whole system event based we need to make an event every time a message is queued or stays in queue after failing to win the contention window
        msg = tracked_message(message , current_time , medium )
        if target != -1 :
            msg.set_target_node(target)
        self.transmit_buffer.append(msg)

        
    def get_uid(self):
        return self.uid
    
    def transmit_message(self , current_time , medium_asking):
        first_instance = True
        seocnd_instance = True
        msg_to_be_sent = None
        temp = []
        for i in range(len(self.transmit_buffer)):
            msg = self.transmit_buffer[i]
            if msg.target_medium == medium_asking :
                if self.isAP and msg.target_node != -1:
                    if msg.target_node == self.timeslotOwner:
                        if first_instance:
                            msg.set_delay_to_deliver(current_time)
                            self.transmit_history.append(msg)
                            msg_to_be_sent = msg
                            first_instance = False
                        else:
                            if seocnd_instance:
                                msg.set_wait_in_queue(current_time)
                                seocnd_instance = False
                                temp.append(msg)
                            else:
                                temp.append(msg)
                    else:
                        temp.append(msg)
                else:    
                    if first_instance:
                        msg.set_delay_to_deliver(current_time)
                        self.transmit_history.append(msg)
                        msg_to_be_sent = msg
                        first_instance = False
                    else:
                        if seocnd_instance:
                            msg.set_wait_in_queue(current_time)
                            seocnd_instance = False
                            temp.append(msg)
                        else:
                            temp.append(msg)
            else:
                temp.append(msg)
        self.transmit_buffer = temp 
        return msg_to_be_sent.message

    def is_ready_transmit(self , medium_asking ):
        if (not self.transmit_buffer == []) and (self.can_transmit or self.has_beacon_packet() or self.has_downlink()):
            for msg in self.transmit_buffer:
                if msg.target_medium == medium_asking:
                    return True
        return False

#access point functions
    def send_beacon(self , current_time):
        if(current_time%self.beacon_order ==  0):
            msg = "control " + "beaconMac:"+str(self.uid)+"tdma-sch:" + str(self.timeslots[0])  
            for i in range(1,len(self.timeslots)):
                msg = msg + "," + str(self.timeslots[i]) 
            self.transmit_buffer.append(tracked_message(msg  , current_time , 1))
        self.set_timeslot_owner(current_time)

    def has_beacon_packet(self):
        for packet in self.transmit_buffer:
            if packet.message.startswith("control beaconMac:"):
                return True
        return False
    def set_timeslot_owner(self , current_time):
        current_time_slot = int((current_time%self.beacon_order)/5)
        self.timeslotOwner = self.timeslots[current_time_slot]
    
    def has_downlink(self):
        for packet in self.transmit_buffer:
            if  packet.target_node == self.timeslotOwner:
                return True
        return False
    

#bc we have dual link we can send downlink data at same timeslot they have reserved.
#msgs need to be taged with destination