import queue
from collections import deque
import logging
import time
import threading
from config import LOG_FILE

class LogController:
    def __init__(self,app):
        self.app = app
    
        self.t_array = deque([0], maxlen=200)
        self.pressure_deque = deque([0],maxlen=200)
        self.temperature_deque = deque([0],maxlen=200)
        self.stopthread = threading.Event()
        self.t_start = time.time()
        
        self.log_queue = queue.Queue()      
        self.thermocouplethread = threading.Thread(target=self.record_data, args=(self.stopthread,self.log_queue,self.t_array, self.t_start, self.pressure_deque, self.temperature_deque))

        self.thermocouplethread.start()

    def record_data(self, stopthread, log_queue, t_array,  t_start, pressure_deque,temperature_deque):
        while not stopthread.is_set():
            measurement_start_time = time.perf_counter()
            
            tempdata = self.app.temp_controller.read_thermocouples()
            pressuredata = self.app.pressure_controller.read_pressure()
            record = logging.LogRecord(name="", level=20, pathname=LOG_FILE, lineno=0,msg=str(tempdata + [pressuredata]), args=None, exc_info=None)
            log_queue.put(record)

            temperature_deque.append(tempdata)
            pressure_deque.append(round(pressuredata, 5))
            t_array.append(time.time() - t_start)
            
            measurement_end_time = time.perf_counter()
            duration = measurement_end_time-measurement_start_time
            if 0.5-duration > 0:
                time.sleep(0.5-duration)

    def close(self):
        self.stopthread.set()
        self.thermocouplethread.join()
        print("Logger Closing")
