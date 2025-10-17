import tkinter as tk
from tkinter import filedialog
import csv


## Manual Control Panel
# Load files and display recipe
# Generate a sub-panel if manual valve opening/closing is required

class ManualControlPanel:
    def __init__(self, app):
        self.app = app
        self.BG_COLOR = app.BG_COLOR
        self.BORDER_COLOR = app.BORDER_COLOR
        self.FONT = app.FONT
        self.TEXT_COLOR = app.TEXT_COLOR
        self.BUTTON_STYLE = app.BUTTON_STYLE

        self.label = None
        self.csv_panel = None
        self.pulse_length = tk.DoubleVar(value=0.02)  # Default pulse length

    def create_manual_controls(self, parent):
        self.panel = tk.Frame(parent, bg=self.BG_COLOR, width=700, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        parent.add(self.panel)

        # Manual Control Button
        tk.Button(
            self.panel, text="Manual Control", font=self.FONT, bg=self.TEXT_COLOR, relief=self.BUTTON_STYLE,
            command=self.open_manual_control
        ).pack(padx=10, pady=5, anchor=tk.NW)

        # Load File Button
        tk.Button(self.panel, text="Load File", font=self.FONT, bg=self.TEXT_COLOR, relief=self.BUTTON_STYLE, command=self.load_file).pack(padx=(10,350), pady=5, anchor=tk.NW)
        self.label = tk.Label(self.panel, text="", bg=self.BG_COLOR, font=self.FONT)
        self.label.pack(padx=20, pady=5, side=tk.TOP, anchor=tk.NW)

        

    def load_file(self):
        # open file from dialog
        file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("CSV Files", "*.csv")]) 
        if file_path:
            # update the label to show the file name
            self.label.config(text=file_path.split('/')[-1])

            # update the ald_controller's file reference
            self.app.ald_controller.file = file_path

            # display the CSV content
            self.display_csv(file_path)

    def display_csv(self, file_path):
        if self.csv_panel:
            self.csv_panel.destroy() # clear any previous data
        self.csv_panel = tk.Text(self.panel, wrap=tk.NONE, bg=self.TEXT_COLOR, height=10)
        self.csv_panel.pack(fill=tk.BOTH, expand=True)
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    self.csv_panel.insert(tk.END, "\t".join(row) + "\n")
        except Exception as e:
            self.csv_panel.insert(tk.END, f"Error reading file: {e}")

    # creates sub-panel
    def open_manual_control(self):
        manual_control_window = tk.Toplevel(self.app)
        manual_control_window.title("Manual Control")
        manual_control_window.geometry("400x300")
        manual_control_window.configure(bg=self.BG_COLOR)

        # pulse length entry
        pulse_frame = tk.Frame(manual_control_window, bg=self.BG_COLOR, pady=10)
        pulse_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(pulse_frame, text="Pulse Length (s):", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT, padx=5)
        tk.Entry(pulse_frame, textvariable=self.pulse_length, width=10, font=self.FONT).pack(side=tk.LEFT, padx=5)

        # valve controls - calls on valve_controller to trigger ald valves
        for valve_name, task in zip(self.app.valve_controller.valvechannels.keys(), self.app.valve_controller.tasks):
            frame = tk.Frame(manual_control_window, bg=self.BG_COLOR, pady=10)
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=valve_name, bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT, padx=5)
            tk.Button(
                frame, text="Open", font=self.FONT, bg=self.TEXT_COLOR, relief=self.BUTTON_TEXT_COLOR,
                command=lambda t=task: self.app.valve_controller.open_valve(t)
            ).pack(side=tk.LEFT, padx=5)
            tk.Button(
                frame, text="Close", font=self.FONT, bg=self.TEXT_COLOR, relief=self.BUTTON_TEXT_COLOR,
                command=lambda t=task: self.app.valve_controller.close_valve(t)
            ).pack(side=tk.LEFT, padx=5)
            tk.Button(
                frame, text="Pulse", font=self.FONT, bg=self.TEXT_COLOR, relief=self.BUTTON_TEXT_COLOR,
                command=lambda t=task: self.app.valve_controller.pulse_valve([self.app.valve_controller.tasks.index(t)], self.pulse_length.get())
            ).pack(side=tk.LEFT, padx=5)