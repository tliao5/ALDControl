import queue
from collections import deque
import logging
from controllers import QueueHandler
import time
import threading
from config import SAMPLES_PER_SECOND, LOG_FILE

class log_controller:
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
            tempdata = self.app.temp_controller.read_thermocouples()
            pressuredata = self.app.pressure_controller.read_pressure()
            record = logging.LogRecord(name="", level=20, pathname=LOG_FILE, lineno=0,msg=str(tempdata + [pressuredata]), args=None, exc_info=None)
            log_queue.put(record)

            temperature_deque.append(tempdata)
            pressure_deque.append(round(pressuredata, 5))
            t_array.append(time.time() - t_start)
            
            time.sleep(1/SAMPLES_PER_SECOND)

    def close(self):
        self.stopthread.set()
        self.thermocouplethread.join()
        print("Logger Closing")