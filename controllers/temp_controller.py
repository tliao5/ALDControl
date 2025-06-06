import nidaqmx
from nidaqmx.constants import (
    AcquisitionType,
    CJCSource,
    TemperatureUnits,
    ThermocoupleType,
    LineGrouping
)
import queue
import logging
import time
import threading
from config import HEATER_CHANNELS, TEMP_CHANNELS

class TempController:
    def __init__(self,app):
        # log temperature controller intialized
        print("Temperature Controller Initializing")
        self.app = app
        self.channels = HEATER_CHANNELS
        self.tempchannels = TEMP_CHANNELS

        self.tps = 200 # ticks per second for duty cycles

        self.queues = [queue.Queue() for i in range(len(HEATER_CHANNELS))]
        self.autoset_queue = queue.Queue()
        self.current_temp_queue = queue.Queue()
        self.tasks = self.create_heater_tasks()
        self.threads = self.start_threads()
        self.thermocoupletask = self.create_thermocouple_tasks()
        print("Temperature Controller Initialized")

    def create_heater_tasks(self):
        tasks = [nidaqmx.Task(f"Heater {i+1}") for i in range(len(HEATER_CHANNELS))]
        for i in range(len(HEATER_CHANNELS)):
            tasks[i].do_channels.add_do_chan(self.channels[f"h{i+1}channel"], line_grouping=LineGrouping.CHAN_PER_LINE)
        return tasks

    def start_threads(self):
        # Create Duty Cycle threads
        self.stopthread = threading.Event()
        self.autoset = threading.Event()
        duty_cycles = [threading.Thread() for i in range(len(HEATER_CHANNELS))]
        duty_cycles[0] = threading.Thread(target=self.autoset_duty_cycle, args=(self.stopthread, self.queues[0], self.tasks[0], self.tps))
        duty_cycles[0].start()
        for i in range(len(HEATER_CHANNELS)-1):
            duty_cycles[i+1] = threading.Thread(target=self.duty_cycle, args=(self.stopthread, self.queues[i+1], self.tasks[i+1], self.tps))
            duty_cycles[i+1].start()
        return duty_cycles
    
    def create_thermocouple_tasks(self):
        self.app.logger.info("main reactor,inlet lower, inlet upper, exhaust,TMA,Trap,Gauges")
        tempchannels = ["ai0", "ai1", "ai2", "ai3", "ai4", "ai5", "ai6"]
        task = nidaqmx.Task("Thermocouple")
        for channel_name in tempchannels:
            task.ai_channels.add_ai_thrmcpl_chan(
                f"cDaq1Mod1/{channel_name}", min_val=0.0, max_val=200.0,
                units=TemperatureUnits.DEG_C, thermocouple_type=ThermocoupleType.K,
                cjc_source=CJCSource.CONSTANT_USER_VALUE, cjc_val=20.0
            )
        task.start()
        return task
    
    def read_thermocouples(self):
        return self.thermocoupletask.read()

    #def log_temps

    def autoset_duty_cycle(self,stopthread, duty_queue, task, tps):
        task.start()
        voltageold = False # default voltage state
        duty_queue.put(0) # default duty
        current_temp = 0
        autoset_temp = 0
        while not stopthread.is_set(): # loop until tc.stopthread.set()
            if not duty_queue.empty(): # check for updates in queue
                set_duty = duty_queue.get(block=False)
            
            if not self.current_temp_queue.empty(): # check for updates in queue
               current_temp = self.current_temp_queue.get(block=False)
            if not self.autoset_queue.empty(): # check for updates in queue
                autoset_temp = self.autoset_queue.get(block=False)
            
            if self.autoset.is_set() and current_temp > autoset_temp - 0.5:
                duty = set_duty-1
            else:
                duty = set_duty
            #print(f"Current Temp: {current_temp}, Autoset Temp: {autoset_temp}, Autoset: {self.autoset.is_set()}")
            #print(f"Duty : {duty}")
            # Duty Cycle
            for i in range(tps):
                voltage = i < duty
                if voltageold != voltage: # check if voltage should change from 1->0 or 0->1
                    voltageold = voltage
                    task.write(voltage) # send update signal to DAQ
                    #print(f"{task.name}: "+str(voltage))
                time.sleep(1/tps)
        
        # Close tasks after loop is told to stop by doing tc.stopthread.set() in main program
        task.write(False)
        task.stop()
        print(f"Task {task.name}: Task Closing, Voltage set to False")
        task.close()
    
    def duty_cycle(self,stopthread, duty_queue, task, tps):
        task.start()
        voltageold = False # default voltage state
        duty_queue.put(0) # default duty
        while not stopthread.is_set(): # loop until tc.stopthread.set()
            if not duty_queue.empty(): # check for updates in queue
                duty = duty_queue.get(block=False)

            # Duty Cycle
            for i in range(tps):
                voltage = i < duty
                if voltageold != voltage: # check if voltage should change from 1->0 or 0->1
                    voltageold = voltage
                    task.write(voltage) # send update signal to DAQ
                    #print(f"{task.name}: "+str(voltage))
                time.sleep(1/tps)
        
        # Close tasks after loop is told to stop by doing tc.stopthread.set() in main program
        task.write(False)
        task.stop()
        print(f"Task {task.name}: Task Closing, Voltage set to False")
        task.close()

    def update_duty_cycle(self, queue, duty):
        try:
            duty_value = int(duty.get()) ## fix back when updating for ttk interface
            if 0 <= duty_value <= self.tps:
                print(f"Duty cycle updated {duty_value}")
                # log duty cycle updated
                while not queue.empty():
                    queue.get()
                    print("get")
                queue.put(duty_value)
                return duty_value
            else:
                raise Exception()
        except:
            print(f"Invalid Input. Please enter an integer between 0 and {self.tps}.")   # turn into a log warning
            queue.put(0)
            return 0
  
    def close(self):
        self.stopthread.set()
        for t in self.threads[::]: t.join()
        self.thermocoupletask.close()
        print("Thermocouple Task closing")
