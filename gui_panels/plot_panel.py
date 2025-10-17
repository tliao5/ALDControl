import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from collections import deque
import time
import logging

# colors for Show Temperature function, needs to have at least as many colors as thermocouples to display
THERMOCOUPLE_COLORS = ["b","g","r","c","m","y","k","steelblue","fuchsia","navy","peru","lawngreen"]

class PlotPanel:
    def __init__(self, app):
        self.app = app
        self.BG_COLOR = app.BG_COLOR
        self.BORDER_COLOR = app.BORDER_COLOR
        self.FONT = app.FONT
        self.TEXT_COLOR = app.TEXT_COLOR
        self.BUTTON_TEXT_COLOR = app.BUTTON_TEXT_COLOR
        self.BUTTON_STYLE = app.BUTTON_STYLE
        self.ON_COLOR = app.ON_COLOR
        self.OFF_COLOR = app.OFF_COLOR
        self.Y_MIN_DEFAULT = app.Y_MIN_DEFAULT
        self.Y_MAX_DEFAULT = app.Y_MAX_DEFAULT
        self.SENSOR_NAMES = app.SENSOR_NAMES
        self.TEMP_CHANNELS = app.TEMP_CHANNELS

        self.fig, self.ax, self.ax_right, self.pressure, self.t_array, self.t_start, self.sensors = self.plot_initialize()
        self.ymin = tk.StringVar(value=self.Y_MIN_DEFAULT)
        self.ymax = tk.StringVar(value=self.Y_MAX_DEFAULT)
        self.show_temperatures = False

    def create_plot_panel(self, title):
        frame = tk.Frame(bg=self.TEXT_COLOR, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.plot_data = []

        # call to start plot animation
        ani = animation.FuncAnimation(self.fig, self.animate, interval=250, save_count=150, repeat=True)
        plot = FigureCanvasTkAgg(self.fig, frame)
        plot.draw()
        plot.get_tk_widget().grid(row=0, column=0, rowspan=40, columnspan=30, padx=10, pady=10, sticky=tk.NSEW)

        toolbar_frame = tk.Frame(master=frame)
        toolbar_frame.grid(row=41, column=0, columnspan=30, pady=5)

        # dynamic setting of y-scale minimum and maximum
        row = tk.Frame(frame, bg=self.TEXT_COLOR)
        row.grid(row=frame.grid_size()[1], column=0, columnspan=frame.grid_size()[0], pady=10)
        tk.Label(row, text="y-min:", relief=self.BUTTON_STYLE, bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(row, width=10, textvariable=self.ymin, font=self.FONT).pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="y-max:", relief=self.BUTTON_STYLE, bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(row, width=10, textvariable=self.ymax, font=self.FONT).pack(side=tk.LEFT, padx=5)
        
        # Show Temperatures Button
        self.show_temperatures_button = tk.Button(
            row, text='Show Temperatures OFF', fg=self.BUTTON_TEXT_COLOR, bg=self.OFF_COLOR, relief=self.BUTTON_STYLE,  font=self.FONT,
            command=self.toggle_show_temperatures)
        self.show_temperatures_button.pack(padx=5)

        return frame

    def plot_initialize(self):
        
        # Plot Settings
        plt.rcParams["figure.figsize"] = [13.00, 4.00]
        plt.rcParams["figure.autolayout"] = True
        plt.rcParams['font.size'] = 20


        fig, ax = plt.subplots()
        ax_right = ax.twinx() # right-hand temperature axis
        pressure = self.app.log_controller.pressure_deque
        t_start = self.app.log_controller.t_start
        t_array = self.app.log_controller.t_array
        sensors = self.SENSOR_NAMES
        return fig, ax, ax_right, pressure, t_array, t_start, sensors

    def animate(self, i):
        try:
            # clear plots for new animation
            self.ax.clear()
            self.ax_right.clear()

            tempdata = self.app.log_controller.temperature_deque[-1] # pull last entry from temperature deque

            self.ax.plot(self.t_array, self.pressure,linewidth=1.5) # plot pressure
            
            # if Show Temperatures is active, plot temperature
            if self.show_temperatures == True:
                self.ax_right.set_visible(True) 
                self.ax_right.set_ylim(0,300) # maybe make the right-hand temperature y-scale dynamic also?
                for i in range(len(self.TEMP_CHANNELS)):
                    self.ax_right.plot(self.t_array, [row[i] for row in self.app.log_controller.temperature_deque],THERMOCOUPLE_COLORS[i])
            else:
                self.ax_right.set_visible(False) 

            ymin = float(self.ymin.get())
            ymax = float(self.ymax.get())
            self.ax.set_ylim(ymin, ymax)
            self.ax.set_title("ALD Run Monitor")
            self.ax.set_xlim(left=self.t_array[0], right=self.t_array[0] + 300) # make sure x_limits update with data

            # display thermocouple values based on formula
            for j, sensor in enumerate(self.sensors[:-1]):
                y_position = ymin + (ymax - ymin) * (0.05 + 0.07 * j)
            
                if self.show_temperatures == True:
                    color = THERMOCOUPLE_COLORS
                else:
                    color = ['k']*(len(self.sensors)-1)
            
                self.ax.text(self.t_array[0] + 225, y_position, f"{sensor}, {str(tempdata[j])[:5]}", color=color[j], fontsize=14)
                self.fig.tight_layout()
        except Exception as e:
            logging.error("Error during animation: %s", e)

    # turn Show Temperatures on and off
    def toggle_show_temperatures(self):
        if self.show_temperatures_button['text'] == 'Show Temperatures ON':
            self.show_temperatures = False
            self.show_temperatures_button.config(text='Show Temperatures OFF', bg=self.OFF_COLOR)
        elif self.show_temperatures_button['text'] == 'Show Temperatures OFF':
            self.show_temperatures = True
            self.show_temperatures_button.config(text='Show Temperatures ON', bg=self.ON_COLOR)

    # cleanup
    def close(self):
        plt.close(self.fig)

