import tkinter as tk
from nidaqmx import Task
from nidaqmx.constants import LineGrouping
from config import *
from controllers import log_controller

class MainPower:
    def __init__(self, app):
        self.app = app
        self.task = self.create_main_power_task()

    def create_main_power_task(self):
        task = Task("Main Power")
        task.do_channels.add_do_chan(MAIN_POWER_CHANNEL, line_grouping=LineGrouping.CHAN_PER_LINE)
        task.start()
        task.write(False)
        task.stop()
        return task

    def create_main_power_button(self, parent):
        self.main_power_button = tk.Button(
            parent, text='Main Power OFF', fg=BUTTON_TEXT_COLOR, bg=OFF_COLOR, relief=BUTTON_STYLE,
            command=self.toggle_main_power
        )
        self.main_power_button.pack(pady=10)

    def toggle_main_power(self):
        if self.main_power_button.config('text')[-1] == 'Main Power ON':
            self.main_power_off()
        else:
            self.main_power_on()

    def main_power_off(self):
        self.task.start()
        self.task.write(False)
        self.task.stop()
        self.main_power_button.config(text='Main Power OFF', bg=OFF_COLOR)
        record = log_controller.create_record(f"MP, 0",MONITOR_LOG_FILE)
        self.app.log_controller.monitor_queue.put(record)
        
    def main_power_on(self):
        self.task.start()
        self.task.write(True)
        self.task.stop()
        self.main_power_button.config(text='Main Power ON', bg=ON_COLOR)
        record = log_controller.create_record(f"MP, 1",MONITOR_LOG_FILE)
        self.app.log_controller.monitor_queue.put(record)

    def close(self):
        self.task.write(False)
        self.task.close()
