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

        self.queues = self.create_heater_queue()
        self.tasks = self.create_heater_tasks()
        self.threads = self.start_threads()
        self.thermocoupletask = self.create_thermocouple_tasks()

    def create_heater_queue(self):
        h1queue = queue.Queue()
        h2queue = queue.Queue()
        h3queue = queue.Queue()
        return [h1queue,h2queue,h3queue]

    def create_heater_tasks(self):
        h1task = nidaqmx.Task("Heater 1")
        h2task = nidaqmx.Task("Heater 2")
        h3task = nidaqmx.Task("Heater 3")

        h1task.do_channels.add_do_chan(self.channels["h1channel"], line_grouping=LineGrouping.CHAN_PER_LINE)
        h2task.do_channels.add_do_chan(self.channels["h2channel"], line_grouping=LineGrouping.CHAN_PER_LINE)
        h3task.do_channels.add_do_chan(self.channels["h3channel"], line_grouping=LineGrouping.CHAN_PER_LINE)
        return [h1task,h2task,h3task]

    def start_threads(self):
        # Create Duty Cycle threads
        self.stopthread = threading.Event()

        h1dutycycle = threading.Thread(target=self.duty_cycle, args=(self.stopthread, self.queues[0], self.tasks[0], self.tps))
        h2dutycycle = threading.Thread(target=self.duty_cycle, args=(self.stopthread, self.queues[1], self.tasks[1], self.tps))
        h3dutycycle = threading.Thread(target=self.duty_cycle, args=(self.stopthread, self.queues[2], self.tasks[2], self.tps))
        h1dutycycle.start()
        h2dutycycle.start()
        h3dutycycle.start()
        return [h1dutycycle,h2dutycycle,h3dutycycle]
    
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
                print("Duty cycle updated")
                # log duty cycle updated
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