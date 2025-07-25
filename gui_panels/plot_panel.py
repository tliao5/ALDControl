import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from collections import deque
import time
import logging
from config import *

THERMOCOUPLE_COLORS = ["b","g","r","c","m","y","k","steelblue","fuchsia","navy","peru","lawngreen"]

class PlotPanel:
    def __init__(self, app):
        self.app = app
        self.fig, self.ax, self.ax_right, self.pressure, self.t_array, self.t_start, self.sensors = self.plot_initialize()
        self.ymin = tk.StringVar(value=Y_MIN_DEFAULT)
        self.ymax = tk.StringVar(value=Y_MAX_DEFAULT)
        self.show_temperatures = False

    def create_plot_panel(self, title):
        frame = tk.Frame(bg=TEXT_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.temp_plot_data = []

        ani = animation.FuncAnimation(self.fig, self.animate, interval=250, save_count=150, repeat=True)
        tempplot = FigureCanvasTkAgg(self.fig, frame)
        tempplot.draw()
        tempplot.get_tk_widget().grid(row=0, column=0, rowspan=40, columnspan=30, padx=10, pady=10, sticky=tk.NSEW)

        toolbar_frame = tk.Frame(master=frame)
        toolbar_frame.grid(row=41, column=0, columnspan=30, pady=5)
        #NavigationToolbar2Tk(tempplot, toolbar_frame)

        row = tk.Frame(frame, bg=TEXT_COLOR)
        row.grid(row=frame.grid_size()[1], column=0, columnspan=frame.grid_size()[0], pady=10)
        tk.Label(row, text="y-min:", relief=BUTTON_STYLE, bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(row, width=10, textvariable=self.ymin, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="y-max:", relief=BUTTON_STYLE, bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(row, width=10, textvariable=self.ymax, font=FONT).pack(side=tk.LEFT, padx=5)
        self.show_temperatures_button = tk.Button(
            row, text='Show Temperatures OFF', fg=BUTTON_TEXT_COLOR, bg=OFF_COLOR, relief=BUTTON_STYLE,  font=FONT,
            command=self.toggle_show_temperatures)
        self.show_temperatures_button.pack(padx=5)

        return frame

    def plot_initialize(self):
        plt.rcParams["figure.figsize"] = [13.00, 4.00]
        plt.rcParams["figure.autolayout"] = True
        plt.rcParams['font.size'] = 20
        fig, ax = plt.subplots()
        ax.locator_params(tight=True,nbins=500)
        ax_right = ax.twinx()
        pressure = self.app.log_controller.pressure_deque
        t_start = self.app.log_controller.t_start
        t_array = self.app.log_controller.t_array
        sensors = SENSOR_NAMES
        return fig, ax, ax_right, pressure, t_array, t_start, sensors

    def animate(self, i):
        try:
            self.ax.clear()
            self.ax_right.clear()

            tempdata = self.app.log_controller.temperature_deque[-1]
            

            self.ax.plot(self.t_array, self.pressure,linewidth=1.5)
            
            if self.show_temperatures == True:
                self.ax_right.set_visible(True) 
                self.ax_right.set_ylim(0,300)
                for i in range(len(THERMOCOUPLE_CHANNELS):
                    self.ax_right.plot(self.t_array, [row[i] for row in self.app.log_controller.temperature_deque],THERMOCOUPLE_COLORS[i])
            else:
                self.ax_right.set_visible(False) 

            ymin = float(self.ymin.get())
            ymax = float(self.ymax.get())
            self.ax.set_ylim(ymin, ymax)
            self.ax.set_yscale('log')
            self.ax.set_title("ALD Run Monitor")
            self.ax.set_xlim(left=self.t_array[0], right=self.t_array[0] + 300)

            for j, sensor in enumerate(self.sensors[:-1]):
                y_position = ymin * (ymax / ymin) ** (0.05 + 0.07 * j)
                if self.show_temperatures == True:
                    color = THERMOCOUPLE_COLORS
                else:
                    color = ['k']*7
                self.ax.text(self.t_array[0] + 200, y_position, f"{sensor}, {str(tempdata[j])[:5]}",color=color[j])
            self.fig.tight_layout()
        except Exception as e:
            logging.error("Error during animation: %s", e)

    def toggle_show_temperatures(self):
        if self.show_temperatures_button['text'] == 'Show Temperatures ON':
            self.show_temperatures = False
            self.show_temperatures_button.config(text='Show Temperatures OFF', bg=OFF_COLOR)
        elif self.show_temperatures_button['text'] == 'Show Temperatures OFF':
            self.show_temperatures = True
            self.show_temperatures_button.config(text='Show Temperatures ON', bg=ON_COLOR)

    def close(self):
        plt.close(self.fig)
