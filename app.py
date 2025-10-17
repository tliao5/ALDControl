import tkinter as tk

from config import *
from gui_panels.main_power import MainPower
from gui_panels.heater_control_panel import HeaterControlPanel
from gui_panels.plot_panel import PlotPanel
from gui_panels.ald_panel import ALDPanel
from gui_panels.manual_control_panel import ManualControlPanel
from controllers.valve_controller import ValveController
from controllers.temp_controller import TempController
from controllers.pressure_controller import PressureController
from controllers.ald_controller import ALDController
from controllers.mfc_reader import AlicatController
from controllers.log_controller import LogController

import logging
class ALDApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ALD Control")

        self.state("zoomed")
        self.configure(bg=BG_COLOR)
        
        # Logging output setup
        # create formatters
        formatter = logging.Formatter(fmt='%(asctime)s %(message)s',datefmt='%m/%d %H:%M:%S')
        monitor_formatter = logging.Formatter( fmt='%(asctime)s.%(msecs)03d %(message)s',datefmt='%m/%d %H:%M:%S')

        # logger for general application logs
        self.logger = logging.getLogger('main_logger')
        self.logger.propagate=False
        self.logger.setLevel(logging.INFO)
        logger_handler = logging.FileHandler(LOG_FILE)
        logger_handler.setFormatter(formatter)
        self.logger.addHandler(logger_handler)

        self.monitor_logger = logging.getLogger('monitor')
        self.monitor_logger.propagate=False
        self.monitor_logger.setLevel(logging.DEBUG)
        monitor_handler = logging.FileHandler(MONITOR_LOG_FILE)
        monitor_handler.setFormatter(monitor_formatter)
        self.monitor_logger.addHandler(monitor_handler)

        # Initialize controllers
        self.valve_controller = ValveController()
        self.temp_controller = TempController(self)
        self.pressure_controller = PressureController()
        self.ald_controller = ALDController(self)
        self.log_controller = LogController(self)

        self.temp_controller.start_threads()

        self.alicat = alicat = AlicatController(port=MFC_PORT)
        #self.alicat.change_setpoint(setpoint_value=0.0)

        # Initialize components
        self.main_power = MainPower(self)
        self.heater_control_panel = HeaterControlPanel(self)
        self.plot_panel = PlotPanel(self)
        self.ald_panel = ALDPanel(self)
        self.manual_control_panel = ManualControlPanel(self)

        self.create_layout()
        print("ALD Control GUI Initialized")
        self.logger.info("ALD Control GUI Initialized")

    def create_layout(self):
        # outer frame contains all other frames
        outer_frame = tk.Frame(self, bg=BG_COLOR, highlightbackground=TEXT_COLOR, highlightthickness=5)
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # top pane - main power switch
        top_pane = tk.PanedWindow(outer_frame, orient=tk.VERTICAL, bg=BG_COLOR, bd=0, sashwidth=2, sashpad=0)
        top_pane.pack(fill=tk.BOTH, expand=True)

        # main power button
        top_frame = tk.Frame(top_pane, bg=BG_COLOR, height=50, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.main_power.create_main_power_button(top_frame)
        top_pane.add(top_frame)

        # main content area - will contain plot_panel and heater_control_panel
        main_pane = tk.PanedWindow(top_pane, orient=tk.VERTICAL, bg=BG_COLOR, bd=0, sashwidth=5)
        main_pane.grid_rowconfigure(0, weight=1)
        main_pane.grid_columnconfigure(0, weight=1)
        top_pane.add(main_pane)

        # sets up the two areas for plot_panel and heater_control_panel
        horizontal_pane = tk.PanedWindow(main_pane, orient=tk.HORIZONTAL, bg=BG_COLOR, bd=0, sashwidth=5)
        main_pane.add(horizontal_pane)
        horizontal_pane.add(self.plot_panel.create_plot_panel("Left Panel Plot"))
        horizontal_pane.add(self.heater_control_panel.create_heater_control_panel())
        horizontal_pane.grid_rowconfigure(0, weight=1)
        horizontal_pane.grid_columnconfigure(0, weight=1)
        horizontal_pane.grid_columnconfigure(1, weight=1)

        # bottom content area - will contain manual_control_panel and ald_panel
        bottom_pane = tk.PanedWindow(main_pane, orient=tk.HORIZONTAL, bg=BG_COLOR, bd=0, sashwidth=5, height=300)
        main_pane.add(bottom_pane)
        self.manual_control_panel.create_manual_controls(bottom_pane)
        self.ald_panel.create_ald_panel(bottom_pane)

    def on_closing(self):
        print("GUI closing")
        self.log_controller.close()
        self.plot_panel.close()
        self.heater_control_panel.close()
        self.temp_controller.close()
        self.pressure_controller.close()
        self.ald_controller.close()
        self.main_power.close()
        self.valve_controller.close()
        
        self.destroy()
        print("Program Closed")
        self.logger.info("ALD Control GUI Closed")


if __name__ == "__main__":
    gui = ALDApp()
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)
    gui.mainloop()

