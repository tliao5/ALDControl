import pandas as pd
import numpy as np
import logging
from controllers import log_controller
import time
import threading
import queue

from config import MONITOR_LOG_FILE

## ALD Controller
# Creates new thread to run recipe
# Pauses if signalled to by ald_panel
# Interfaces with valve_controller to do the actual opening/closing/pulsing of valves

class ALDController:
    def __init__(self, app):
        print("ALD Recipe Controller Initializing")
        self.app = app
        self.stopthread = threading.Event()
        self.queue = queue.Queue()
        print("ALD Recipe Controller Initialized")
        
    def create_run_thread(self,loops,vc):
        self.aldRunThread = threading.Thread(target=self.aldRun, args=(loops, vc, self.queue, self.app.log_controller.log_queue, self.app.log_controller.monitor_queue))
        self.aldRunThread.start()

    ### 
    # aldRun(file, loops, gvc) - executes an ALD Run
    # file - recipe file read in to program
    # loops - number of times to loop through the recipe
    # vc - gas_valve_controller() object
    ###
    def aldRun(self, loops, vc, queue, log_queue, monitor_queue):
        data = pd.read_csv(self.file)
        dataNP = data.to_numpy()
        elapsed_time = 0
        print(vc.tasks)
        print(dataNP)
        # log run starting and recipe order
        print("Run Starting")
        record = log_controller.create_record("Run Starting",MONITOR_LOG_FILE)
        monitor_queue.put(record)
        previndices = []
        for i in range(loops): #This is the number of loops the user wants to iterate the current file (ie - number of ALD cycles)
            if self.app.ald_panel.pause_run_event.is_set():
                vc.close_all()
                while self.app.ald_panel.pause_run_event.is_set() and not self.stopthread.is_set():
                    time.sleep(0.25)
            if self.stopthread.is_set():
                    break

            #print(f"Cycle: {i+1}/{loops}")

#### The following logic is a little overcomplicated, but theoretically enables a valve to be held open / multiple valves pulsed at once ####
##      It does do the simple task of pulsing the valves based on run recipe, but the other features have not been tested
            
            for j in range(0,len(dataNP),1):# for each row in the .csv file, we want to set the experimental parameters accordingly
                #print(f"Row: {j+1}")
                if self.stopthread.is_set():
                    break
                row = dataNP[j][:-1].tolist()
                indices = [index for index, val in enumerate(row) if val == 1] # find the indices of each "1" in the line, indicating valve should be opened
                indices = [index for index in indices if index not in previndices] # this checks if the previous line in the recipe file indicates a valve should be held open instead of pulsed
                
                if indices: # send a log entry to the monitor log file saying which valve has been triggered
                    valve_names = " ".join([f"AV0{i+1}" for i in indices])
                    record = log_controller.create_record(f"{valve_names}, {dataNP[j][6]}",MONITOR_LOG_FILE)
                    monitor_queue.put(record)
                    vc.pulse_valve(indices,dataNP[j][6])
                else: # if there are no valves being pulsed, assume the system is purging and send a log entry
                    record = log_controller.create_record(f"Purge, {dataNP[j][6]}",MONITOR_LOG_FILE)
                    monitor_queue.put(record)
                    time.sleep(dataNP[j][6])
                previndices = indices
                elapsed_time = elapsed_time+dataNP[j][6] # update elapsed time for progress tracking in ald_panel
                queue.put(elapsed_time)
                #print()
        print("Run Over")
        record = log_controller.create_record(f"ALD Run Finished - {loops} Cycles", MONITOR_LOG_FILE)
        monitor_queue.put(record)
        vc.close_all() # extra safety check that all ald valves are shut at the end of a run

    def close(self):
        self.stopthread.set()
        # Check if the thread exists and is initialized
        if hasattr(self, 'aldRunThread') and self.aldRunThread is not None:
            print("Waiting for ALD Run Thread to Close")
            self.aldRunThread.join() # call thread to close
        print("ALD Recipe Controller Closing")
