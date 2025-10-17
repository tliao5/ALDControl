import nidaqmx
from nidaqmx.constants import LineGrouping
import queue
import logging
import time
import threading
from config import PRESSURE_CHANNEL

## Pressure Controller
# More of a pressure reader
# Sets up nidaqmx to read the MKS Baratron
# read_pressure called by log_controller

class PressureController:
    def __init__(self):
        print("Pressure Controller Initializing")
        pressure_sensor_channel = PRESSURE_CHANNEL
        self.ptask = nidaqmx.Task("Pressure")
        self.ptask.ai_channels.add_ai_voltage_chan(pressure_sensor_channel["Pchannel"], min_val=-10.0, max_val=10.0)
        self.ptask.start()
        #log pressure controller initialized
        print("Pressure Controller Initialized")

    def read_pressure(self):
        voltage = self.ptask.read()
        pressure = voltage/10
        return pressure
    
    def readPressure_pdr2000(self):
        self.ptask.start(0)
        voltage = self.ptask.read()
        pressure = 0.01*10**(2*voltage)*.001 #from pdr manual
        logging.info("pressure is " + str(pressure))
        self.ptask.stop()
        return pressure
    
    def close(self):
        self.ptask.close()
        print("Pressure Task Closing")