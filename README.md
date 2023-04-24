# Mac-simulator-Py
a small mac simulator used to evaluate mac(medium access control) protocols performance
currentyly testing a simple fixed TDMA scheme.
work in progress:
multi-base station support required
channels need to handle collisions differently

there are 2 types of sch_task :
1.tasks which perform on nodes
2.tasks whcich on scheduler it self or mediums

can't do carrier sense with other tasks because it becomes dependant on order of execution,and it also shows if medium is used in previous timeunit
solution :
1.do it as a different process after (or before) resolving tranmissions in mediums
2.add a priority modifier to tasks so it will be performed after all other tasks
3.make a differnt task queue for post process tasks which is always executed after the normal queue
