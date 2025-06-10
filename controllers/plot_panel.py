import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from collections import deque
import time
import logging
from config import *

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
        self.line = None  # Line object for blitting

    def create_plot_panel(self, title):
        frame = tk.Frame(bg=TEXT_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Initialize the line for blitting
        self.line, = self.ax.plot([], [], lw=2)  # Create an empty line object

        # Use blitting in FuncAnimation
        ani = animation.FuncAnimation(
            self.fig, self.animate, interval=250, blit=True, save_count=150, repeat=True
        )
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
        t_array = self.app.log_controller.t_array
        pressure = self.app.log_controller.pressure_deque
        t_start = self.app.log_controller.t_start
        sensors = ["main reactor", "inlet lower", "inlet upper", "exhaust", "TMA", "Trap", "Gauges", "Pressure"]
        return fig, ax, pressure, t_array, t_start, sensors

    def animate(self, i):
        try:
            # Process the queue without blocking
            while not self.app.log_controller.log_queue.empty():
                self.app.logger.handle(self.app.log_controller.log_queue.get(block=False))
            
            # Update line data
            self.line.set_data(self.t_array, self.pressure)
    
            # Get current axis limits
            ymin = float(self.ymin.get())
            ymax = float(self.ymax.get())
            x_min = self.t_array[0]
            x_max = self.t_array[0] + 300
    
            # Check if axis limits have changed
            if self.ax.get_ylim() != (ymin, ymax):
                self.ax.set_ylim(ymin, ymax)
                self.ax.set_yscale('log')  # Ensure log scale is applied
                y_ticks = [ymin, (ymin + ymax) / 2, ymax]  # Example: 3 ticks (min, mid, max)
                self.ax.set_yticks(y_ticks)
                self.ax.set_yticklabels([f"{tick:.2e}" for tick in y_ticks])  # Format as scientific notation
    
            if self.ax.get_xlim() != (x_min, x_max):
                self.ax.set_xlim(left=x_min, right=x_max)
                x_ticks = [x_min, x_min + 150, x_max]  # Example: 3 ticks
                self.ax.set_xticks(x_ticks)
                self.ax.set_xticklabels([f"{tick:.0f}" for tick in x_ticks])  # Format as integers
    
            # Update y-axis label dynamically (optional, if label changes)
            self.ax.set_ylabel("Pressure (log scale)")  # Example label, update as needed
    
            # Manage text annotations dynamically
            text_artists = []  # List to store text objects
            tempdata = self.app.log_controller.temperature_deque[-1]
            for j, sensor in enumerate(self.sensors[:-1]):
                y_position = ymin * (ymax / ymin) ** (0.4 + 0.07 * j)
                text = self.ax.text(
                    self.t_array[0] + 250, y_position, f"{sensor}, {str(tempdata[j])[:5]}"
                )
                text_artists.append(text)  # Add text object to the list
    
            # Return the updated line object and text objects for blitting
            return [self.line] + text_artists
        except Exception as e:
            logging.error("Error during animation: %s", e)
            return []

    def close(self):
        plt.close(self.fig)
