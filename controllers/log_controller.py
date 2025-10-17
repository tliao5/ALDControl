import queue
from collections import deque
import logging
import time
import threading
from config import LOG_FILE, MONITOR_LOG_FILE

## Log Controller
# Gathers data from sensors
# Sends data to plot_panel
# Manages temperature watchdog and autoset functions
# Interfaces with temp_controller to do so

class LogController:
    def __init__(self,app):
        self.app = app
    
        self.max_temperatures = [300]*4 # default max temperature, will cause problems if this is below the starting system temp
        self.controllers_active_flag = False # this flag is set to False on startup or when overheat is detected
                                            # otherwise the log thread would spam messages until the overheat was resolved
                                            # main_power will set this flag to True when the system is initializing, and when power is turned on after an overheat
       
        # declaring data deques
        self.t_array = deque([], maxlen=200) # time array
        self.pressure_deque = deque([],maxlen=200) # pressure data
        self.temperature_deque = deque([],maxlen=200) # thermocouple data
        self.stopthread = threading.Event() # stopthread for logging thread 
        self.t_start = time.time() # time of initialization
        
        self.log_queue = queue.Queue() # holds log records waiting to be processed from threads
        self.monitor_queue = queue.Queue()  # holds monitor log records '''
        
        # this function can probably be edited so the arguments are not so wordy, but it works for now
        self.logging_thread = threading.Thread(target=self.record_data, args=(self.stopthread,self.log_queue,self.t_array, self.t_start, self.pressure_deque, self.temperature_deque))
        self.logging_thread.start()

    # this thread gathers all data and puts the log records into their files
    def record_data(self, stopthread, log_queue, t_array,  t_start, pressure_deque,temperature_deque):
        while not stopthread.is_set():
            measurement_start_time = time.perf_counter() # performance timer to make sure each log entry at standard timing every 0.5 seconds
            
            tempdata = self.app.temp_controller.read_thermocouples() # get temperature data
            pressuredata = self.app.pressure_controller.read_pressure() # get pressure data
            record = create_record(str(tempdata + [pressuredata]), LOG_FILE) 
            self.app.logger.handle(record) # log to main log file
            
            # send main reactor temp to Heater 1 thread for autoset
            try:
                while True:
                    self.app.temp_controller.current_temp_queue.get_nowait() # clear temperature queue
            except:
                pass
            self.app.temp_controller.current_temp_queue.put(tempdata[0]) # put most recent temperature value on the queue
            
            # update monitor log file
            while not self.monitor_queue.empty():
                self.app.monitor_logger.handle(self.monitor_queue.get(block=False))
            
            
            # Kill ald run, close valves, -- flow controller will continue to be on, and logging/plotting will continue 
            if self.controllers_active_flag == True: # only check for overheat if main power is enabled/re-enabled
                ''' key: ["main reactor", "inlet lower", "inlet upper", "exhaust", "TMA", "Trap", "Gauges"] '''
                if tempdata[0] > self.max_temperatures[0]:
                    self.app.logger.warning(f"SYSTEM OVERHEAT - Main Reactor {tempdata[0]} > {self.max_temperatures[0]}")
                    record = create_record(f"SYSTEM OVERHEAT - Main Reactor {tempdata[0]} > {self.max_temperatures[0]}", MONITOR_LOG_FILE)
                    self.monitor_queue.put(record)
                    self.kill_run()
                if tempdata[5] > self.max_temperatures[1]:
                    self.app.logger.warning(f"SYSTEM OVERHEAT - Trap {tempdata[5]} > {self.max_temperatures[1]}")
                    record = create_record(f"SYSTEM OVERHEAT - Trap {tempdata[5]} > {self.max_temperatures[1]}", MONITOR_LOG_FILE)
                    self.monitor_queue.put(record)
                    self.kill_run()
                if max(tempdata[1],tempdata[2],tempdata[4]) > self.max_temperatures[2]:
                    self.app.logger.warning(f"SYSTEM OVERHEAT - Inlet Lower, Inlet Upper, TMA {tempdata[1]},{tempdata[2]},{tempdata[4]} > {self.max_temperatures[2]}")
                    record = create_record(f"SYSTEM OVERHEAT - Inlet Lower, Inlet Upper, TMA {tempdata[1]},{tempdata[2]},{tempdata[4]} > {self.max_temperatures[2]}", MONITOR_LOG_FILE)
                    self.monitor_queue.put(record)
                    self.kill_run()
                if max(tempdata[3],tempdata[6]) > self.max_temperatures[3]:
                    self.app.logger.warning(f"SYSTEM OVERHEAT - Gauges, Exhaust {tempdata[3]},{tempdata[6]} > {self.max_temperatures[3]}")
                    record = create_record(f"SYSTEM OVERHEAT - Gauges, Exhaust {tempdata[3]},{tempdata[6]} > {self.max_temperatures[3]}", MONITOR_LOG_FILE)
                    self.monitor_queue.put(record)
                    self.kill_run()
                    
            
            # send data to plot_panel
            temperature_deque.append(tempdata)
            pressure_deque.append(round(pressuredata, 5))
            t_array.append(time.time() - t_start)
            
            measurement_end_time = time.perf_counter()
            duration = measurement_end_time-measurement_start_time
            if 0.5-duration > 0:
                time.sleep(0.5-duration)
                # wait until 0.5 seconds is up before logging again
        print("Logging Thread Stopped")

    # called by heater_control_panel to set a new max temp value for comparison
    def update_max_temp(self, i, max_temp):
        self.max_temperatures[i] = max_temp

    # pauses ALD run and turns off main power
    def kill_run(self):
        self.app.main_power.main_power_off()
        if hasattr(self.app.ald_controller, 'aldRunThread') and self.app.ald_controller.aldRunThread is not None:
            self.app.ald_panel.pause_run()
        self.controllers_active_flag = False
        
    # cleanup
    def close(self):
        print("Logging Thread Closing")
        self.stopthread.set()
        self.logging_thread.join()
        print("Logging Thread Closed")


def create_record(message,pathname):
    record = logging.LogRecord(name="", level=20, pathname=pathname, lineno=0,msg=message, args=None, exc_info=None)
    return record

