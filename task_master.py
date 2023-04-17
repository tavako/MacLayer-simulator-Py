from sch_task import sch_task
class task_master:
    def __init__(self , approx_tasks ,all_nodes ):
        self.tasks = [None] * approx_tasks 
        self.task_counter = 0
        self.all_nodes = all_nodes

    def add_task(self , task):
        if self.task_counter >= len(self.tasks):
            self.tasks.append(task)
        else:
            self.tasks[self.task_counter] = task
        self.task_counter += 1 

    def finished(self):
        return  self.task_counter == 0

    def exec_step(self , tick):
        temp = []
        for i in range(self.task_counter) :
            task = self.tasks[i]
            if task.get_exec_time() == tick:
                if task.m_type == "queue_message":
                    temp.append(sch_task(tick+1 , "transmit_pending" , [task.args[0]]))
                    self.task_counter += 1
                if task.m_type == "transmit_pending":
                    task.reset_task(tick + 1)
                    temp.append(task)
                    continue
                task.execute(self.all_nodes , tick)
                self.task_counter -= 1
            else:
                temp.append(task)
        self.tasks = temp
        del temp
    
    # it only removes one at a time so other tasks can continue
    def remove_filler(self , target):
        for i in range(len(self.tasks)):
            task = self.tasks[i]
            if task.m_type == "transmit_pending" and task.args[0] == target:
                del(self.tasks[i])
                self.task_counter -= 1
                break
# read events from file , database 
    def laod_from_file(self,name):
        file1 = open(name, 'r')
        lines = file1.readlines()
        for line in lines:
            parts = line.split("_")
            if parts[1] == "msg":
                self.add_task(sch_task(parts[0] ,"queue_message", [parts[2] , parts[3]]))
            elif parts[1] == "sndbc":
                self.add_task(sch_task(parts[0] , "send_beacon" , [parts[2]]))
            elif parts[1] == "logRcv":
                self.add_task(sch_task(parts[0] , "show_recieved" , [parts[2]]))
        file1.close()

    def sort_scheduled_tasks(self):
        self.tasks.sort(key = lambda x : x.get_exec_time() , reverse=False)
    
    def get_earliest_event(self):
        self.sort_scheduled_tasks()
        if len(self.tasks) != 0:
            return self.tasks[0].get_exec_time()
        return "no-task-available"
