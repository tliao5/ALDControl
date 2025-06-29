import queue
from collections import deque
import logging
import time
import threading
from config import LOG_FILE, MONITOR_LOG_FILE

class LogController:
    def __init__(self,app):
        self.app = app
    
        self.max_temperatures = [100]*4
        self.controllers_active_flag = True

        self.t_array = deque([0], maxlen=200)
        self.pressure_deque = deque([0],maxlen=200)
        self.temperature_deque = deque([0],maxlen=200)
        self.stopthread = threading.Event()
        self.t_start = time.time()
        
        self.log_queue = queue.Queue()     
        self.monitor_queue = queue.Queue() 
        self.logging_thread = threading.Thread(target=self.record_data, args=(self.stopthread,self.log_queue,self.t_array, self.t_start, self.pressure_deque, self.temperature_deque))

        self.logging_thread.start()

    def record_data(self, stopthread, log_queue, t_array,  t_start, pressure_deque,temperature_deque):
        while not stopthread.is_set():
            measurement_start_time = time.perf_counter()
            
            tempdata = self.app.temp_controller.read_thermocouples()
            pressuredata = self.app.pressure_controller.read_pressure()
            record = create_record(str(tempdata + [pressuredata]), LOG_FILE)
            self.app.logger.handle(record)
            while not self.monitor_queue.empty():
                self.app.monitor_logger.handle(self.monitor_queue.get(block=False))
            
            # Kill ald run, close valves, -- flow controller will continue to be on, and logging/plotting will continue 
            #print(self.controllers_active_flag
            if self.controllers_active_flag == True:
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

            temperature_deque.append(tempdata)
            pressure_deque.append(round(pressuredata, 5))
            t_array.append(time.time() - t_start)
            
            measurement_end_time = time.perf_counter()
            duration = measurement_end_time-measurement_start_time
            if 0.5-duration > 0:
                time.sleep(0.5-duration)
        print("Logging Thread Stopped")

    def update_max_temp(self, i, max_temp):
        self.max_temperatures[i] = max_temp

    def kill_run(self):
        self.app.main_power.main_power_off()
        if hasattr(self.app.ald_controller, 'aldRunThread') and self.app.ald_controller.aldRunThread is not None:
            self.app.ald_panel.pause_run()
        self.controllers_active_flag = False
        

    def close(self):
        print(self.stopthread.is_set())
        print("Logging Thread Closing")
        self.stopthread.set()
        print(self.stopthread.is_set())
        self.logging_thread.join()
        print("Logging Thread Closed")


def create_record(message,pathname):
    record = logging.LogRecord(name="", level=20, pathname=pathname, lineno=0,msg=message, args=None, exc_info=None)
    return record
