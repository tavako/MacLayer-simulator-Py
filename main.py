from medium import Medium
from node_dualLink import Node
from task_master import task_master
from sch_task import sch_task
import matplotlib.pyplot as plt
from datetime import date
import numpy as np
import math
#quality measurements
average_delay  = 0 
std_deviation_delay = 0
avg_backoff = 0
timeout_rate = 0
channel_utilization = 0
QoS_improvement_ratio = 0
avg_delay_in_node = 0
#multiple medium , node , event simulation 
tick_counter = 0
all_nodes = []
#-----simulation params
# each tick equals how many micro seconds in real case
simulation_scale  = 1000
max_tick = 1000
sim_hopping_enabled = True


def pull_for_node_events(all_nodes , scheduler ):
    for node in all_nodes:
        while node.events != [] :
            scheduler.add_task(node.events.pop())

def tick_to_real(time_stamp):
    return time_stamp*simulation_scale

ins_medium = Medium(12000 , "air(wireless)" , 1)
ins_medium_downlink = Medium(12000 , "air(wireless)" , 0)
node1 = Node(0)
node1.isAP = True
node2 = Node(1)
node3 = Node(2)
all_nodes.append(node1)
all_nodes.append(node2)
all_nodes.append(node3)
ins_taskmaster = task_master(20 , all_nodes)
ins_medium.add_batch_subscriber(all_nodes)
ins_medium_downlink.add_batch_subscriber(all_nodes)
for i in range(0,1000,1):
    ins_taskmaster.add_task(sch_task(i , "send_beacon" , [0]))

ins_taskmaster.add_task(sch_task(130 , "queue_message" , [1  ,"hello , I'm dead." ]))
ins_taskmaster.add_task(sch_task(140 , "queue_message" , [2  ,"I don't care." ]))
ins_taskmaster.add_task(sch_task(268 , "queue_message" , [1  ,"you are dead , too" ]))
ins_taskmaster.add_task(sch_task(240 , "queue_message" , [2  ,"oh , now I'm worried." ]))

while tick_counter < max_tick:
    ins_taskmaster.exec_step(tick_counter)
    transmitted_nodes = ins_medium.resolve_requests(tick_counter)
    transmitted_nodes_downlink = ins_medium_downlink.resolve_requests(tick_counter)
    ins_taskmaster.remove_filler(transmitted_nodes)
    ins_taskmaster.remove_filler(transmitted_nodes_downlink)
    pull_for_node_events(all_nodes , ins_taskmaster)
    # can check for empty task master and impending messages for early termination 
    if ins_taskmaster.finished():
        print("EARLY-TERMINATION/terminated at step :", tick_counter )
        break 
    tick_counter += 1
    if sim_hopping_enabled:
        tick_counter  =  ins_taskmaster.get_earliest_event()
    
    

#visualize events on timeline 

time_line = list(range(0,max_tick+1))
y_placements = [0] * len(time_line)

fig,ax = plt.subplots()
xs = []
messages = []
plt.scatter(time_line , y_placements)
plt.ylim((-0.1 , 1))
for packet in node1.recieved_packets:
    xs.append(packet.time_stamp)
    messages.append(packet.message)
    plt.bar(packet.time_stamp,0.48  , color = "red")

annot = ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="->"))
annot.set_visible(False)
sc = plt.scatter(xs ,[0.5]*len(xs) ,marker="*" , s=50)
def update_annot(ind):
    
    pos = sc.get_offsets()[ind["ind"][0]]
    annot.xy = pos
    text = "{}".format(" ".join([messages[n] for n in ind["ind"]]))
    annot.set_text(text)
def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = sc.contains(event)
        if cont:
            update_annot(ind)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
fig.canvas.mpl_connect("motion_notify_event", hover)
plt.show()


# stats extraction
data_point_counter = 0
for m_node in all_nodes:
    for data_point in  m_node.transmit_history:
        if not data_point.message.startswith("control"):
            average_delay += data_point.delay_to_deliver
            data_point_counter += 1
            avg_delay_in_node += data_point.wait_in_queue
if data_point_counter > 0 :
    average_delay = average_delay/data_point_counter
for m_node in all_nodes:
    for data_point in  m_node.transmit_history:
        if not data_point.message.startswith("control"):
            std_deviation_delay += (average_delay-data_point.delay_to_deliver)**2
if data_point_counter>0 :
    std_deviation_delay = math.sqrt(std_deviation_delay/data_point_counter)
    avg_delay_in_node = avg_delay_in_node/data_point_counter
all_nodes[1].print_packets()
print("stats report:")
print("average_delay:{} , std delay:{} , average delay in queue:{}".format(average_delay, std_deviation_delay , avg_delay_in_node ))