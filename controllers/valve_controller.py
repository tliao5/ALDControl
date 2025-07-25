import nidaqmx
from nidaqmx.constants import LineGrouping
import time
import threading
from config import VALVE_CHANNELS

## Valve Controler
# Create nidaqmx channels for each valve based on VALVE_CHANNELS
# Open / Close / Pulse / Close_All different valve functions

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
        return valves

    def open_valve(self,task):
        task.write(True)
        time.sleep(0.1)
        #log valve opened?
        
    def close_valve(self,task):
        task.write(False)
        time.sleep(0.1)
        #log valve closed?

#### This pulse valve function can theoretically allow multiple valve to be pulsed simultaneously
##      doing so seems to cause significant latency, but for now it performs the simple function good enough
    def pulse_valve(self,indices,pulse_length):
        tasks = [self.tasks[i] for i in indices]
        for t in tasks[::]:
            t.write(True)
            measurement_start_time = time.perf_counter()
        time.sleep(pulse_length)
        for t in tasks[::]:
            t.write(False)
            measurement_end_time = time.perf_counter()
        #log valve pulsed?

    # simple function to close all valves at once
    def close_all(self):
        for task in self.tasks[::]:
            #print(task)
            task.write(False)
            time.sleep(0.1)

    # cleanup
    def close(self):
        self.close_all()
        for task in self.tasks[::]: task.close()
        print("Valve Controller Tasks Closing")
