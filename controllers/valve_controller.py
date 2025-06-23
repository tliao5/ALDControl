import nidaqmx
from nidaqmx.constants import LineGrouping
import time
import threading
from config import VALVE_CHANNELS

# creating a valve_controller object will setup all relevant channels
# access said object in order to run methods on the valves connected to channels defined below

# currently hard coded for the three valves of this ALD system
class ValveController:
    def __init__(self):
        print("Valve Controller Initialized")
        self.valvechannels = VALVE_CHANNELS
        self.tasks = self.create_valve_tasks()
        # log valve controller initialized
        print("Valve Controller Initialized")
        
    def create_valve_tasks(self):
        valves = [nidaqmx.Task(f"AV0{i+1}") for i in range(len(VALVE_CHANNELS))]
        for i in range(len(VALVE_CHANNELS)):
            valves[i].do_channels.add_do_chan(self.valvechannels[f"AV0{i+1}"], line_grouping=LineGrouping.CHAN_PER_LINE)
            valves[i].start()
            print(valves)
        return valves

        
    def open_valve(self,task):
        task.write(True)
        time.sleep(0.1)
        #log valve opened
        
    def close_valve(self,task):
        task.write(False)
        time.sleep(0.1)
        #log valve closed

    def pulse_valve(self,indices,pulse_length):
        
        #print(indices[::])
        tasks = [self.tasks[i] for i in indices]
        #print(tasks)
        for t in tasks[::]:
            #print(t.name)
            t.write(True)
            measurement_start_time = time.perf_counter()
            
            
        time.sleep(pulse_length)
        for t in tasks[::]:
            #print(t.name)
            
            t.write(False)
            measurement_end_time = time.perf_counter()
            print(measurement_end_time-measurement_start_time)
        
        
        #print(f"Task {task.name}: False")
        #log valve pulsed

    def close_all(self):
        for task in self.tasks[::]:
            print(task)
            #task.write(False)
            time.sleep(0.1)

    def close(self):
        self.close_all()
        for task in self.tasks[::]: task.close()
        print("Valve Controller Tasks Closing")
