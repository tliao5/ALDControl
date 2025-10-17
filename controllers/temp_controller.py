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
from controllers import log_controller
import time
import threading
from config import HEATER_CHANNELS, TEMP_CHANNELS, MONITOR_LOG_FILE, DUTY_CYCLE_LENGTH, SENSOR_NAMES

## Temperature Controller
# Creates nidaqmx tasks for each heater based on HEATER_CHANNELS
# Creates one nidaqmx task for the thermocouples, from TEMP_CHANNELS
#
# Important Components:
#   Each heater has a corresponding thread, this is set dynamically based on HEATER_CHANNELS
#   Duty cycle and autoset are set from heater_control_panel
#   Max temp monitoring from log_controller
#   Only Heater 1 has autoset and it runs on a slightly different duty cycle function

TICKS_PER_CYCLE = 100
class TempController:
    def __init__(self,app):
        # log temperature controller intialized
        print("Temperature Controller Initializing")
        self.app = app
        self.channels = HEATER_CHANNELS
        self.tempchannels = TEMP_CHANNELS

        self.ticks_per_cycle = TICKS_PER_CYCLE # ticks per second for duty cycles

        self.queues = [queue.Queue() for i in range(len(HEATER_CHANNELS))] # queues for thread communication
        self.autoset_queue = queue.Queue() # contains True/False whether or not autoset is enabled/disabled
        self.current_temp_queue = queue.Queue() # updated from log_controller, grabs most recent main reactor temperature
        self.tasks = self.create_heater_tasks()
        self.thermocoupletask = self.create_thermocouple_tasks()
        print("Temperature Controller Initialized")

    def create_heater_tasks(self):
        tasks = [nidaqmx.Task(f"H{i+1}") for i in range(len(HEATER_CHANNELS))]
        for i in range(len(HEATER_CHANNELS)):
            tasks[i].do_channels.add_do_chan(self.channels[f"h{i+1}channel"], line_grouping=LineGrouping.CHAN_PER_LINE)
        return tasks

    def start_threads(self):
        # Create Duty Cycle threads
        self.stopthread = threading.Event()
        self.autoset = threading.Event()
        duty_cycles = [threading.Thread() for i in range(len(HEATER_CHANNELS))]
        duty_cycles[0] = threading.Thread(target=self.autoset_duty_cycle, args=(self.stopthread, self.queues[0], self.app.log_controller.monitor_queue, self.tasks[0], self.ticks_per_cycle))
        duty_cycles[0].start()
        for i in range(len(HEATER_CHANNELS)-1):
            duty_cycles[i+1] = threading.Thread(target=self.duty_cycle, args=(self.stopthread, self.queues[i+1], self.app.log_controller.monitor_queue, self.tasks[i+1], self.ticks_per_cycle))
            duty_cycles[i+1].start()
        self.threads = duty_cycles
    
    def create_thermocouple_tasks(self):
        self.app.logger.info(SENSOR_NAMES)
        tempchannels = TEMP_CHANNELS
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
        
    def autoset_duty_cycle(self,stopthread, duty_queue, log_queue, task, ticks_per_cycle):
        task.start()
        voltageold = False # default voltage state
        duty_queue.put(0) # default duty
        current_temp = 0
        autoset_temp = 0
        duration = 0
        record = log_controller.create_record(f"{task.name} Started",MONITOR_LOG_FILE)
        log_queue.put(record)
        while not stopthread.is_set(): # loop until stopthread.set()
            measurement_start_time = time.perf_counter()
            if not duty_queue.empty(): # check for updates in queue
                set_duty = duty_queue.get(block=False)

            # Autoset logic
            # compare current temp to setpoint temp
            # if current temp is too high, temporarily lower duty by 1, checks every cycle
            if not self.current_temp_queue.empty(): # check for updates in queue
               current_temp = self.current_temp_queue.get(block=False)
            if not self.autoset_queue.empty(): # check for updates in queue
                autoset_temp = self.autoset_queue.get(block=False)
                #print(f"New Autoset Found: {autoset_temp}")
            
            if self.autoset.is_set() and current_temp > autoset_temp + 0.5:
                duty = set_duty-1
            else:
                duty = set_duty

            # Check Autoset
            #print(f"Current Temp: {current_temp}, Autoset Temp: {autoset_temp}, Autoset: {self.autoset.is_set()}")
            #print(f"Duty : {duty}")
            
            # Duty cycle
            # on for duty % of time, sleep for 100-duty % of time
            # send a log record to the monitor log every time the heater is toggled
            # length of duty cycle defined by DUTY_CYCLE_LENGTH in config
            if duty > 0:
                time.sleep((ticks_per_cycle-duty)*DUTY_CYCLE_LENGTH/ticks_per_cycle)
                measurement_end_time = time.perf_counter()
                duration = measurement_end_time-measurement_start_time
                record = logging.LogRecord(name="", level=20, pathname=MONITOR_LOG_FILE, lineno=0,msg=f"{task.name}, 0, {duty}, {round(duration,3)}", args=None, exc_info=None)
                log_queue.put(record)
                task.write(True) # send update signal to DAQ
                measurement_start_time = time.perf_counter()
                time.sleep(duty*DUTY_CYCLE_LENGTH/ticks_per_cycle)
                measurement_end_time = time.perf_counter()
                duration = measurement_end_time-measurement_start_time
                record = logging.LogRecord(name="", level=20, pathname=MONITOR_LOG_FILE, lineno=0,msg=f"{task.name}, 1, {duty}, {round(duration,3)}", args=None, exc_info=None)
                log_queue.put(record)
                task.write(False) # send update signal to DAQ
            else:
                time.sleep(DUTY_CYCLE_LENGTH)

            
        
        # Close tasks after loop is told to stop by doing tc.stopthread.set() in main program
        task.write(False)
        task.stop()
        print(f"Task {task.name}: Task Closing, Voltage set to False")
        record = logging.LogRecord(name="", level=20, pathname=MONITOR_LOG_FILE, lineno=0,msg=f"{task.name} Closed", args=None, exc_info=None)
        log_queue.put(record)
        task.close()
    
    def duty_cycle(self,stopthread, duty_queue, log_queue, task, ticks_per_cycle):
        task.start()
        voltageold = False # default voltage state
        duty_queue.put(0) # default duty
        duration = 0
        record = log_controller.create_record(f"{task.name} Started",MONITOR_LOG_FILE)
        log_queue.put(record)
        while not stopthread.is_set(): # loop until tc.stopthread.set()
            measurement_start_time = time.perf_counter()
            if not duty_queue.empty(): # check for updates in queue
                duty = duty_queue.get(block=False)

            # Duty Cycle
            if duty > 0:
                time.sleep((ticks_per_cycle-duty)*DUTY_CYCLE_LENGTH/ticks_per_cycle)
                measurement_end_time = time.perf_counter()
                duration = measurement_end_time-measurement_start_time
                record = logging.LogRecord(name="", level=20, pathname=MONITOR_LOG_FILE, lineno=0,msg=f"{task.name}, 0, {duty}, {round(duration,3)}", args=None, exc_info=None)
                log_queue.put(record)
                task.write(True) # send update signal to DAQ
                measurement_start_time = time.perf_counter()
                time.sleep(duty*DUTY_CYCLE_LENGTH/ticks_per_cycle)
                measurement_end_time = time.perf_counter()
                duration = measurement_end_time-measurement_start_time
                record = logging.LogRecord(name="", level=20, pathname=MONITOR_LOG_FILE, lineno=0,msg=f"{task.name}, 1, {duty}, {round(duration,3)}", args=None, exc_info=None)
                log_queue.put(record)
                task.write(False) # send update signal to DAQ
            else:
                time.sleep(DUTY_CYCLE_LENGTH)
        
        # Close tasks after loop is told to stop by doing tc.stopthread.set() in main program
        task.write(False)
        task.stop()
        print(f"Task {task.name}: Task Closing, Voltage set to False")
        record = logging.LogRecord(name="", level=20, pathname=MONITOR_LOG_FILE, lineno=0,msg=f"{task.name} Closed", args=None, exc_info=None)
        log_queue.put(record)
        task.close()

    def update_duty_cycle(self, queue, duty):
        try:
            print("tempcontroller")
            if 0 <= duty <= self.ticks_per_cycle:
                print(f"Duty cycle updated {duty}")
                # log duty cycle updated
                while not queue.empty():
                    queue.get()
                queue.put(duty)
                return duty
            else:
                raise Exception()
        except:
            print(f"Invalid Input. Please enter an integer between 0 and {self.ticks_per_cycle}.")   # turn into a log warning
            queue.put(0)
            return 0
  
    def close(self):
        self.stopthread.set()
        for t in self.threads[::]: t.join()
        self.thermocoupletask.close()
        print("Thermocouple Task closing")






