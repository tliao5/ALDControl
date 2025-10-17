import tkinter as tk
from tkinter import ttk
import threading
import pandas as pd


## ALD Panel
# Bottom right panel of the GUI
# Interfaces with the run functions
# Allows user input to enter number of cycles
# Calls on ald_controller to create a new thread to run the recipe
#

# Important components:
#   Number of Cycles entry field
#   Run Progress Bar
#   Pause Run Button

class ALDPanel:
    def __init__(self, app):
        self.app = app
        self.BG_COLOR = app.BG_COLOR
        self.BORDER_COLOR = app.BORDER_COLOR
        self.FONT = app.FONT
        self.TEXT_COLOR = app.TEXT_COLOR
        self.BUTTON_TEXT_COLOR = app.BUTTON_TEXT_COLOR
        self.BUTTON_STYLE = app.BUTTON_STYLE
        self.LOG_FILE = app.LOG_FILE
        self.ON_COLOR = app.ON_COLOR
        self.OFF_COLOR = app.OFF_COLOR
        

        self.runtime = 0 # calculated based on number of loops multiplied by ald cycle time
        self.loops=tk.StringVar() # entry field for number of loops
        self.progresstime = None # local tracker for ALD run progress
        self.progressbar = None # display object to show the green progress bar, also used as the counter for run progress
        
        self.recipe_label = None  # label field for run state
        self.confirm_button = None  # confirm button for run state

        self.pause_run_event = threading.Event() # communication with ald_controller to pause/unpause a run

    def create_ald_panel(self, parent):
        self.ald_panel = tk.Frame(parent, bg=self.BG_COLOR, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        parent.add(self.ald_panel)

        # recipe entry and run button
        recipe_frame = tk.Frame(self.ald_panel, bg=self.BG_COLOR, pady=10)
        recipe_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(recipe_frame, text="Cycles:", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(recipe_frame, textvariable=self.loops, width=10, font=self.FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(
            recipe_frame, text="Run Recipe", font=self.FONT, bg=self.TEXT_COLOR, relief=self.BUTTON_STYLE,
            command=lambda:self.start_run()  # call start_run directly on button press
        ).pack(side=tk.LEFT, padx=5)

        # label field for run state
        self.recipe_label = tk.Label(recipe_frame, text="Status: New Run", bg=self.BG_COLOR, font=self.FONT)
        self.recipe_label.pack(side=tk.LEFT, padx=5)

        # progress bar and time display
        self.progresstime = tk.Label(self.ald_panel, text=f"Time: {self.format_time(0)}", bg=self.BG_COLOR, font=self.FONT)
        self.progresstime.pack(side=tk.LEFT, anchor=tk.NW, padx=20)
        self.progressbar = ttk.Progressbar(self.ald_panel, orient=tk.HORIZONTAL, length=400)
        self.progressbar.pack(pady=5, padx=30, anchor=tk.NW)
        
        # log file
        tk.Label(self.ald_panel, text=f"Log File Output: {self.LOG_FILE}", bg=self.BG_COLOR, font=self.FONT).pack(padx=20, pady=5, side=tk.TOP, anchor=tk.NW)

    # triggered when the Run Recipe button is pressed - calculates cycle time, creates a confirm run button to trigger the ald_controller thread
    def start_run(self):
        try:
            print("Prepping New Run")
            loops = int(self.loops.get())
            # check if a file is loaded
            if not self.app.ald_controller.file:
                self.recipe_label.config(text="Status: Invalid Input")
                return
            # check if loops is not zero
            if loops <= 0:
                self.recipe_label.config(text="Status: Invalid Input")
                return
            # display number of loops
            self.recipe_label.config(text=f"Status: Run for {loops} loops")

            print(loops)

            # calculate runtime based on the entered number of loops
            data = pd.read_csv(self.app.ald_controller.file)
            self.runtime = sum(data.iloc[:, 6]) * loops

            # clear progress bar and progress timer for new run
            self.progressbar["value"] = 0
            self.progresstime.config(text=f"Estimated Time Left: {self.format_time(0)}")
            self.progressbar["max"]=self.runtime+0.001

            # display calculated runtime in the status label
            self.recipe_label.config(text=f"Status: Run for {loops} loops - Estimated Runtime: {self.format_time(self.runtime)}")

            # add Confirm button
            if not self.confirm_button:
                self.confirm_button = tk.Button(
                    self.recipe_label.master, text="Confirm", font=self.FONT, bg=self.ON_COLOR, relief=self.BUTTON_STYLE,
                    command=lambda loops = self.loops : self.confirm_run(loops)
                )
            self.confirm_button.pack(side=tk.LEFT, padx=5)
        except:
            self.recipe_label.config(text="Status: Invalid Input")

    def confirm_run(self, loops):
        # Check if a file is selected
        if not self.app.ald_controller.file:
            self.recipe_label.config(text="Status: Invalid Input")
            return

        # Disable the entry and Run Recipe button in the recipe frame
        recipe_frame = self.recipe_label.master  # Get the parent frame of the recipe label
        for widget in recipe_frame.winfo_children():
            if isinstance(widget, tk.Entry) or (isinstance(widget, tk.Button) and widget.cget("text") == "Run Recipe"):
                widget.config(state=tk.DISABLED)
        # Disable all other buttons in the ALD panel to prevent interference
        for widget in self.ald_panel.winfo_children():
            if isinstance(widget, tk.Button):
                if widget:
                    widget.config(state=tk.DISABLED)
            
        if self.confirm_button:
            self.confirm_button.pack_forget()

        # disable the manual control panel
        for widget in self.app.manual_control_panel.panel.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)

        # create pause button
        self.pause_button = tk.Button(self.recipe_label.master, text="Pause Run", font=self.FONT, bg=self.ON_COLOR, fg=self.BUTTON_TEXT_COLOR, relief=self.BUTTON_STYLE,
                    command=lambda: self.toggle_pause_run())
        self.pause_button.pack(side=tk.LEFT,padx=5)

        # update the label to indicate the run is in progress
        self.recipe_label.config(text="Status: Run in Progress")

        # start the recipe run using the entered number of loops
        self.app.ald_controller.create_run_thread(int(loops.get()), self.app.valve_controller)

        # start Progress Bar countdown
        self.progressbar["value"] = 0
        self.update_progress_bar()
        
        # log run start
        self.app.logger.info(f"Starting New Run - {loops} Cycles")
    
    # toggle between paused and unpaused
    def toggle_pause_run(self):
        if self.pause_button["bg"] == self.ON_COLOR:
            self.pause_run()
        elif self.pause_button["bg"] == self.OFF_COLOR:
            self.unpause_run()
    
    def pause_run(self):
        print("paused")
        self.pause_run_event.set() # communicates to ald_controller to pause
        self.pause_button["bg"] = self.OFF_COLOR
        self.pause_button["text"] = "Unpause Run"
        self.recipe_label["text"]="Status: Run Paused"
    
    def unpause_run(self):
        print("unpaused")
        self.pause_run_event.clear() # communicates to ald_controller to unpause
        self.pause_button["bg"] = self.ON_COLOR
        self.pause_button["text"] = "Pause Run"
        self.recipe_label.config(text="Status: Run in Progress")

    def update_progress_bar(self):
        if self.pause_run_event.is_set():
            self.progressbar.after(900, self.update_progress_bar)
        elif not self.app.ald_controller.queue.empty(): # check for updates in queue - grabs elapsed time calculated by ald_controller
            elapsed_time = int(self.app.ald_controller.queue.get(block=False))
            #print(f"Elapsed Time: {elapsed_time}")
            self.progressbar["value"] = elapsed_time # match progress bar to ald_controller calculated time
            self.progressbar.after(900, self.update_progress_bar)
            self.progresstime["text"] = f"Estimated Time Left: {self.format_time(int(self.runtime - elapsed_time))}"
        elif self.progressbar["value"] + 1 <= self.runtime: # update Progressbar Countdown automatically if there is not a new value from ald_controller
            self.progressbar.step(1)
            self.progresstime["text"] = f"Estimated Time Left: {self.format_time(int(self.runtime - self.progressbar["value"]))}"
            self.progressbar.after(900, self.update_progress_bar)
        else: # run must be over if none of the above conditions match
            self.progressbar["value"] = self.runtime
            self.progresstime["text"] = f"Estimated Time Left: {self.format_time(0)}"

            self.pause_button.pack_forget() # hide pause button

            # re-enable manual control buttons
            self.enable_manual_controls()

            # re-enable the entry and Run Recipe button
            recipe_frame = self.recipe_label.master
            for widget in recipe_frame.winfo_children():
                if isinstance(widget, tk.Entry) or (isinstance(widget, tk.Button) and widget.cget("text") == "Run Recipe"):
                    widget.config(state=tk.NORMAL)

            # display run completion message
            self.recipe_label.config(text="Status: Run Complete!")
            self.app.ald_controller.aldRunThread.join()
            self.app.logger.info("ALD Run Finished")
            
    # helper function for Progress Bar display
    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def disable_manual_controls(self):
        # disable all manual control buttons to prevent interference during the run.
        for widget in self.app.manual_control_panel.panel.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)

    def enable_manual_controls(self):
        # re-enable all manual control buttons after the run is complete.
        for widget in self.app.manual_control_panel.panel.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.NORMAL)
        
