import queue
from log_event import log_event
from tracked_message import tracked_message
from pair import pair
from sch_task import sch_task 
class Node:
    def __init__(self , uid ):
        self.status = "idle"
        self.uid = uid
        self.transmit_history = []
        self.transmit_buffer = []
        self.max_retry_before_timeout = 3
        self.initial_backoff_period = 2 #unit slots 
        self.bits_per_slot = 40
        self.mac_scheme = "tdma-fixed-DualLink"
        self.recieved_packets = []
        self.isAP = False
        self.initialization = True
        self.beacon_order = 100
        self.maxPanId = 1
        self.panMap = []
        self.panId = -1
        self.backoffperiods = [2 ,5 ,7]
        self.timeslots = [None]*20    #18 5-length timeslots and 2 timeslots for rejoin 
        self.timeslots[0] = 0
        self.timeslots[1] = 0
        self.occupied_timeslots = 1
        self.start_rejoin = -10
        self.events = []
        self.can_transmit = False
    
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
                self.transmit_buffer.append(tracked_message("control request_join,beaconMac:" + message.split(":")[1] + "myMac:" + str(self.uid) ,tick_counter , 0 ))
                self.permit_transmit(tick_counter , 35)
                #remember the request and retries when model of channels is more complete
            if message.startswith("control request_join,beaconMac:") and self.isAP:
                clientMac = message[message.find("myMac:")+6:]
                clientpanId = self.maxPanId
                if self.occupied_timeslots < 16:
                    self.occupied_timeslots += 1
                    self.timeslots[self.occupied_timeslots] = clientpanId
                if self.uid == int(message[message.find(":")+1:message.find("myMac")]):
                    self.transmit_buffer.append(tracked_message("control accept_join,beaconMac:" + str(self.uid) + "clientMac:" + str(clientMac) + "clientPanid:" + str(clientpanId) , tick_counter ,1 ))
                self.maxPanId+=1
            if message.startswith("control accept_join,beaconMac:"):
                clientMac_rec = message[message.find("clientMac:")+len("clientMac:") : message.find("clientPanid:")]
                if int(clientMac_rec) == self.uid :
                    self.panId = int(message[message.find("clientPanid:")+len("clientPanid:"):])
            if message.startswith("control "+"joinOpportunity,beaconMac:"):
                if self.panId == -1:
                    self.transmit_buffer.append(tracked_message("control request_join,beaconMac:" + message.split(":")[1] + "myMac:" + str(self.uid), tick_counter , 0 ))
             #check tdma schedule and plan accordingly
            if message.startswith("control "+"tdma-sch:"):
                self.timeslots = message.split(":")[1].split(",")
                self.sch_for_transmit(tick_counter)


    def sch_for_transmit(self , tick_counter):
        for i in range(len(self.timeslots)):
            timeslot = self.timeslots[i]
            if timeslot != "None":
                if int(timeslot) == self.panId :
                    self.events.append(sch_task(tick_counter + (i-2)*5 , "grant_transmit_permit" , [self.uid]))
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

    def queue_message(self , message , current_time):
        #to make whole system event based we need to make an event every time a message is queued or stays in queue after failing to win the contention window
        self.transmit_buffer.append(tracked_message(message , current_time , 0))
        
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
                    msg_to_be_sent = msg
                    first_instance = False
                else:
                    msg.set_wait_in_queue(current_time)
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
        elif  self.start_rejoin == current_time - 9 :
            # we can also give 
            msg = "control " + "tdma-sch:" + str(self.timeslots[0])  
            for i in range(1,len(self.timeslots)):
                msg = msg + "," + str(self.timeslots[i]) 
            self.transmit_buffer.append(tracked_message(msg  , current_time , 1))