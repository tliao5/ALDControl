import tkinter as tk
from tkinter import ttk
from config import *
import threading
import pandas as pd

class ALDPanel:
    def __init__(self, app):
        self.app = app

        self.runtime = 0
        self.loops=tk.StringVar()
        self.progressbar = None
        self.progresstime = None
        self.recipe_entry = tk.StringVar()  # Entry field for recipe loops
        self.recipe_label = None  # Label field for run state
        self.confirm_button = None  # Confirm button for run state
        self.pause_run_event = threading.Event()

    def create_ald_panel(self, parent):
        self.ald_panel = tk.Frame(parent, bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        parent.add(self.ald_panel)

        # Recipe Entry and Run Button
        recipe_frame = tk.Frame(self.ald_panel, bg=BG_COLOR, pady=10)
        recipe_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(recipe_frame, text="Cycles:", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(recipe_frame, textvariable=self.loops, width=10, font=FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(
            recipe_frame, text="Run Recipe", font=FONT, bg=TEXT_COLOR, relief=BUTTON_STYLE,
            command=lambda:self.start_run()  # Call start_run directly on button press
        ).pack(side=tk.LEFT, padx=5)

        # Label Field for Run State
        self.recipe_label = tk.Label(recipe_frame, text="Status: New Run", bg=BG_COLOR, font=FONT)
        self.recipe_label.pack(side=tk.LEFT, padx=5)

        # Progress Bar and Time Display
        self.progresstime = tk.Label(self.ald_panel, text=f"Time: {self.format_time(0)}", bg=BG_COLOR, font=FONT)
        self.progresstime.pack(side=tk.LEFT, anchor=tk.NW, padx=20)
        self.progressbar = ttk.Progressbar(self.ald_panel, orient=tk.HORIZONTAL, length=400)
        self.progressbar.pack(pady=5, padx=30, anchor=tk.NW)
        
        # Log File
        tk.Label(self.ald_panel, text=f"Log File Output: {LOG_FILE}", bg=BG_COLOR, font=FONT).pack(padx=20, pady=5, side=tk.TOP, anchor=tk.NW)

    def start_run(self):
        try:
            print("Prepping New Run")
            loops = int(self.loops.get())
            # Check if a file is loaded
            if not self.app.ald_controller.file:
                self.recipe_label.config(text="Status: Invalid Input")
                return
            if loops == 0:
                self.recipe_label.config(text="Status: Invalid Input")
                return
            # Dynamically update loops variable from the entry field
            self.recipe_label.config(text=f"Status: Run for {loops} loops")

            print(loops)

            # Calculate runtime based on the entered number of loops
            data = pd.read_csv(self.app.ald_controller.file)
            self.runtime = sum(data.iloc[:, 6]) * loops

            # Clear progress bar and progress timer
            self.progressbar["value"] = 0
            self.progresstime.config(text=f"Estimated Time Left: {self.format_time(0)}")
            self.progressbar["max"]=self.runtime+0.001

            # Display calculated runtime in the status label
            self.recipe_label.config(text=f"Status: Run for {loops} loops - Estimated Runtime: {self.format_time(self.runtime)}")

            # Add Confirm Button
            if not self.confirm_button:
                self.confirm_button = tk.Button(
                    self.recipe_label.master, text="Confirm", font=FONT, bg=ON_COLOR, relief=BUTTON_STYLE,
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

        # Disable the manual control panel
        for widget in self.app.manual_control_panel.panel.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)
        print("test")

        self.pause_button = tk.Button(self.ald_panel, text="Pause Run", font=FONT, bg=ON_COLOR, relief=BUTTON_STYLE,
                    command=lambda: self.toggle_pause_run())
        self.pause_button.pack(side=tk.LEFT,padx=5)

        # Update the label to indicate the run is in progress
        self.recipe_label.config(text="Status: Run in Progress")

        # Start the recipe run using the entered number of loops
        self.app.ald_controller.create_run_thread(int(loops.get()), self.app.valve_controller)

        # Calculate runtime based on the entered number of loops
        self.progressbar["value"] = 0
        self.update_progress_bar()
        
        # Log run start
        self.app.logger.info("Starting New Run")
    
    def toggle_pause_run(self):
        if self.pause_button["bg"] == ON_COLOR:
            self.pause_run()
        elif self.pause_button["bg"] == OFF_COLOR:
            self.unpause_run()
    
    def pause_run(self):
        print("paused")
        self.pause_run_event.set()
        self.pause_button["bg"] = OFF_COLOR
    
    def unpause_run(self):
        print("unpaused")
        self.pause_run_event.clear()
        self.pause_button["bg"] = ON_COLOR

    def update_progress_bar(self):
        if self.pause_run_event.is_set():
            self.progressbar.after(900, self.update_progress_bar)
        elif not self.app.ald_controller.queue.empty(): # check for updates in queue
            elapsed_time = int(self.app.ald_controller.queue.get(block=False))
            #print(f"Elapsed Time: {elapsed_time}")
            self.progressbar["value"] = elapsed_time
            self.progressbar.after(900, self.update_progress_bar)
            self.progresstime["text"] = f"Estimated Time Left: {self.format_time(int(self.runtime - elapsed_time))}"
        elif self.progressbar["value"] + 1 <= self.runtime:
            self.progressbar.step(1)
            self.progresstime["text"] = f"Estimated Time Left: {self.format_time(int(self.runtime - self.progressbar["value"]))}"
            self.progressbar.after(900, self.update_progress_bar)
        else:
            self.progressbar["value"] = self.runtime
            self.progresstime["text"] = f"Estimated Time Left: {self.format_time(0)}"

            self.pause_button.pack_forget()

            # Re-enable manual control buttons
            self.enable_manual_controls()

            # Re-enable the entry and Run Recipe button
            recipe_frame = self.recipe_label.master  # Get the parent frame of the recipe label
            for widget in recipe_frame.winfo_children():
                if isinstance(widget, tk.Entry) or (isinstance(widget, tk.Button) and widget.cget("text") == "Run Recipe"):
                    widget.config(state=tk.NORMAL)

            self.recipe_label.config(text="Status: Run Complete!")
            self.app.ald_controller.aldRunThread.join()
            self.app.logger.info("ALD Run Finished")
            

    def format_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def disable_manual_controls(self):
        """Disable all manual control buttons to prevent interference during the run."""
        for widget in self.app.manual_control_panel.panel.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)

    def enable_manual_controls(self):
        """Re-enable all manual control buttons after the run is complete."""
        for widget in self.app.manual_control_panel.panel.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.NORMAL)
        
