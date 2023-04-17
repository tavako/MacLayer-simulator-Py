class sch_task:
    def __init__(self , exec_time , m_type , args):

        self.exec_time  = exec_time
        self.m_type = m_type
        self.args = args

    def get_exec_time(self):
        return self.exec_time
    def reset_task(self , new_exec_time):
        self.exec_time = new_exec_time
    def execute(self ,all_nodes , current_time ):
        if self.m_type == "queue_message":
            all_nodes[self.args[0]].queue_message(self.args[1] , current_time)
        if self.m_type == "delete_node":
            del all_nodes[self.args[0]]
        if self.m_type == "flush_queue":
            all_nodes[self.args[0]].transmit_buffer.queue.clear()
        if self.m_type == "show_recieved":
            all_nodes[self.args[0]].print_packets()
        if self.m_type == "send_beacon":
            all_nodes[self.args[0]].send_beacon(current_time)
        if self.m_type == "transmit_pending":
            #only a filler to stop early termination for independant tasks
            return 
        if self.m_type == "grant_transmit_permit":
            all_nodes[self.args[0]].permit_transmit(current_time , 5)
        if self.m_type == "remove_transmit_permit":
            all_nodes[self.args[0]].remove_permit()
        
# more events should be handled 