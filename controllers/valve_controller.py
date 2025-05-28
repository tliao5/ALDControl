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
        self.valvechannels = VALVE_CHANNELS
        self.tasks = self.create_valve_tasks()
        # log valve controller initialized
        
    def create_valve_tasks(self):
        AV01 = nidaqmx.Task("AV01")
        AV02 = nidaqmx.Task("AV02")
        AV03 = nidaqmx.Task("AV03")
        AV01.do_channels.add_do_chan(self.valvechannels["AV01"], line_grouping=LineGrouping.CHAN_PER_LINE)
        AV02.do_channels.add_do_chan(self.valvechannels["AV02"], line_grouping=LineGrouping.CHAN_PER_LINE)
        AV03.do_channels.add_do_chan(self.valvechannels["AV03"], line_grouping=LineGrouping.CHAN_PER_LINE)
        return [AV01, AV02, AV03]

        
    def open_valve(self,task):
        task.start()
        task.write(True)
        time.sleep(0.1)
        #log valve opened
        task.stop()
        
    def close_valve(self,task):
        task.start()
        task.write(False)
        time.sleep(0.1)
        #log valve closed
        task.stop()

    def pulse_valve(self,indices,pulse_length):
        #print(indices[::])
        tasks = [self.tasks[i] for i in indices]
        #print(tasks)
        for t in tasks[::]:
            #print(t.name)
            t.start()
            t.write(True)
        time.sleep(pulse_length)
        for t in tasks[::]:
            #print(t.name)
            t.write(False)
            t.stop()
        #print(f"Task {task.name}: False")
        #log valve pulsed

    def close_all(self):
        for task in self.tasks[::]:
            task.start()
            task.write(False)
            time.sleep(0.1)
            task.stop()
        #log valves closed

    def close(self):
        self.close_all()
        for task in self.tasks[::]: task.close()
        print("Valve Controller Tasks Closing")
