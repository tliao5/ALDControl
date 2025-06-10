import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from collections import deque
import time
import logging
from config import *

class PlotPanel:
    def __init__(self, app):
        self.app = app
        self.fig, self.ax, self.pressure, self.t_array, self.t_start, self.sensors = self.plot_initialize()
        self.ymin = tk.StringVar(value=Y_MIN_DEFAULT)
        self.ymax = tk.StringVar(value=Y_MAX_DEFAULT)

    def create_plot_panel(self, title):
        frame = tk.Frame(bg=TEXT_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        ani = animation.FuncAnimation(self.fig, self.animate, interval=250, save_count=150, repeat=True)
        tempplot = FigureCanvasTkAgg(self.fig, frame)
        tempplot.draw()
        tempplot.get_tk_widget().grid(row=0, column=0, rowspan=40, columnspan=30, padx=10, pady=10, sticky=tk.NSEW)

        toolbar_frame = tk.Frame(master=frame)
        toolbar_frame.grid(row=41, column=0, columnspan=30, pady=5)
        NavigationToolbar2Tk(tempplot, toolbar_frame)

        row = tk.Frame(frame, bg=TEXT_COLOR, pady=10)
        row.grid(row=frame.grid_size()[1], column=0, columnspan=frame.grid_size()[0], pady=10)
        tk.Label(row, text="y-min:", relief=BUTTON_STYLE, bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(row, width=10, textvariable=self.ymin, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="y-max:", relief=BUTTON_STYLE, bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(row, width=10, textvariable=self.ymax, font=FONT).pack(side=tk.LEFT, padx=5)

        return frame

    def plot_initialize(self):
        plt.rcParams["figure.figsize"] = [13.00, 4.50]
        plt.rcParams["figure.autolayout"] = True
        plt.rcParams['font.size'] = 14
        fig, ax = plt.subplots()
        pressure = deque([0.1], maxlen=200)
        t_start = time.time()
        t_array = deque([0], maxlen=200)
        sensors = ["main reactor", "inlet lower", "inlet upper", "exhaust", "TMA", "Trap", "Gauges", "Pressure"]
        return fig, ax, pressure, t_array, t_start, sensors

    def animate(self, i):
        try:
            while not self.app.log_controller.log_queue.empty(): # check for updates in queue
                self.app.logger.handle(self.app.log_controller.log_queue.get(block=False))
            tempdata=self.app.log_controller.temperature_deque[-1]
        

            self.ax.clear()
            self.ax.plot(self.t_array, self.pressure)

            ymin = float(self.ymin.get())
            ymax = float(self.ymax.get())
            self.ax.set_ylim(ymin, ymax)
            self.ax.set_yscale('log')
            self.ax.set_title("Pressure Plot")
            self.ax.set_xlim(left=self.t_array[0], right=self.t_array[0] + 300)

            for j, sensor in enumerate(self.sensors[:-1]):
                y_position = ymin * (ymax / ymin) ** (0.4 + 0.07 * j)
                self.ax.text(self.t_array[0] + 250, y_position, f"{sensor}, {str(tempdata[j])[:5]}")
            self.fig.tight_layout()
        except Exception as e:
            logging.error("Error during animation: %s", e)
    
    def close(self):
        plt.close(self.fig)
