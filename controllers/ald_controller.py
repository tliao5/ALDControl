import pandas as pd
import numpy as np
import logging
import time
import threading

class ALDController:
    def __init__(self):
        self.stopthread = threading.Event()
    ### 
    # aldRun(file, loops, gvc) - executes an ALD Run
    # file - recipe file read in to program
    # loops - number of times to loop through the recipe
    # vc - gas_valve_controller() object
    ###
    def create_run_thread(self,loops,vc):
        self.aldRunThread = threading.Thread(target=self.aldRun, args=(loops, vc))
        self.aldRunThread.start()

    def aldRun(self, loops, vc):
        data = pd.read_csv(self.file)
        dataNP = data.to_numpy()
        print(vc.tasks)
        print(dataNP)
        # log run starting and recipe order
        print("Run Starting")
        previndices = []
        for i in range(loops): #This is the number of loops the user wants to iterate the current file (ie - number of ALD cycles)
            if self.stopthread.isSet():
                    break
            print(f"Cycle: {i+1}/{loops}")
            for j in range(0,len(dataNP),1):#For each row in the .csv file, we want to set the experimental parameters accordingly
                #print(f"Row: {j+1}")
                if self.stopthread.isSet():
                    break
                row = dataNP[j][:-1].tolist()
                indices = [index for index, val in enumerate(row) if val == 1]
                #print(f"Row: {row}, Indices: {indices}, PrevIndices: {previndices}")
                indices = [index for index in indices if index not in previndices]
                if indices:
                    vc.pulse_valve(indices,dataNP[j][6])
                else:
                    #print(f"Purging: {dataNP[j,6]}")
                    time.sleep(dataNP[j][6])
                previndices = indices
                #print()
        print("Run Over")
        vc.close_all() # make sure all valves are shut off at the end of a run

    def close(self):
        self.stopthread.set()
        # Check if the thread exists and is initialized
        if hasattr(self, 'aldRunThread') and self.aldRunThread is not None:
            print("Waiting for ALD Run Thread to Close")
            self.aldRunThread.join()
        print("ALD Recipe Controller Closing")
