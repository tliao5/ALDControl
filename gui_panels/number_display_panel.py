import tkinter as tk
from config import *

class NumberDisplayPanel:
    def __init__(self, app):
        self.app = app
        self.heater_buttons = ["", "", ""]

    def create_number_display_panel(self):
        frame = tk.Frame(bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        d1 = tk.StringVar()
        d2 = tk.StringVar()
        d3 = tk.StringVar()
        d = [d1, d2, d3]

        for i in range(3):
            d[i].set(0)
            row = tk.Frame(frame, bg=BG_COLOR, pady=10)
            row.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(row, text=f"Heater {i+1}:", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
            tk.Entry(row, width=10, font=FONT, textvariable=d[i]).pack(side=tk.LEFT, padx=5)

            button = tk.Button(
                row, text="Set", font=FONT, bg=OFF_COLOR, fg=BUTTON_TEXT_COLOR, relief=BUTTON_STYLE,
                command=lambda i=i: self.set_duty_value(i, d[i])
            )
            button.pack(side=tk.LEFT, padx=5)
            self.heater_buttons[i] = button

        return frame

    def set_duty_value(self, i, duty_cycle_var):
        duty_cycle = int(duty_cycle_var.get())
        if duty_cycle == 0:
            self.heater_buttons[i].config(bg=OFF_COLOR)
        else:
            self.heater_buttons[i].config(bg=ON_COLOR)