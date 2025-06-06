import tkinter as tk
from config import *

class NumberDisplayPanel:
    def __init__(self, app):
        self.app = app
        
    def create_number_display_panel(self):
        frame = tk.Frame(bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        
        self.duty = [tk.StringVar() for i in range(len(HEATER_CHANNELS))]
        
        self.heater_buttons = [tk.Button() for i in range(len(HEATER_CHANNELS))]
        
        # Create heater buttons
        self.heater_buttons = [tk.Button() for i in range(len(HEATER_CHANNELS))]
        for i in range(len(HEATER_CHANNELS)):
            self.duty[i].set(0)
            row = tk.Frame(frame, bg=BG_COLOR, pady=10)
            row.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(row, text=f"Heater {i+1}:", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
            tk.Entry(row, width=10, font=FONT, textvariable=self.duty[i]).pack(side=tk.LEFT, padx=5)

            button = tk.Button(
                row, text="Set", font=FONT, bg=OFF_COLOR, fg=BUTTON_TEXT_COLOR, relief=BUTTON_STYLE,
                command=lambda i=i: self.set_duty_value(i, self.duty[i])
            )
            button.pack(side=tk.LEFT, padx=5)
            self.heater_buttons[i] = button

            # Create autoset buttons
            if i == 0:
                self.autoset_frame = tk.Frame(row,bg=BG_COLOR,pady=10)
                self.autoset_frame.pack(fill=tk.X,padx=5,pady=5)
                autoset_temp=tk.StringVar()
                tk.Entry(self.autoset_frame,width=3,font=FONT,textvariable=autoset_temp).pack(side=tk.LEFT,anchor=tk.NW,padx=(5,2),pady=5)
                tk.Label(self.autoset_frame, text ="°C", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT,anchor=tk.NW,pady=5)
                self.autoset_button = tk.Button(self.autoset_frame,text="Autoset",font=FONT,bg=OFF_COLOR,fg=BUTTON_TEXT_COLOR,relief=BUTTON_STYLE,command=lambda:self.change_autoset(autoset_temp))
                self.autoset_button.pack(side=tk.LEFT,padx=5)
        
        mfc = tk.Frame(frame,bg=BG_COLOR,pady=10)
        mfc.pack(anchor=tk.N,fill=tk.X,padx=10,pady=5)
        setpt=tk.StringVar()
        tk.Label(mfc, text ="Setpoint: ", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT,anchor=tk.NW,padx=5,pady=5)
        tk.Entry(mfc,width=5,font=FONT,textvariable=setpt).pack(side=tk.LEFT,anchor=tk.NW,padx=5,pady=5)
        self.setpoint_button = tk.Button(mfc,text="Change Setpoint",font=FONT,bg=OFF_COLOR,fg=BUTTON_TEXT_COLOR,relief=BUTTON_STYLE,command=lambda:self.change_setpt(setpt))
        self.setpoint_button.pack(side=tk.LEFT,padx=5)
        self.flowrate_label = tk.Label(frame,text="Flowrate: ", bg=BG_COLOR, font=FONT)
        self.flowrate_label.pack(side=tk.TOP,anchor=tk.NW,padx=20,pady=5)
        self.update_setpoint_reading()
            
        tk.Label(frame, text=f"Heater 3 - unused", bg=BG_COLOR, font=FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 2 - Trap", bg=BG_COLOR, font=FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 1 - Chamber", bg=BG_COLOR, font=FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
 
        return frame

    def set_duty_value(self, i, duty_cycle_var):
        duty_value = self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[i],duty_cycle_var)
        if duty_value == 0:
            self.heater_buttons[i].config(bg=OFF_COLOR)
        else:
            self.heater_buttons[i].config(bg=ON_COLOR)
            
    def change_setpt(self,setpt_var):
        try:
            setpt = float(setpt_var.get())
            print(setpt)
            if setpt == 0:
                self.setpoint_button.config(bg=OFF_COLOR)
            elif setpt > 0:
                self.setpoint_button.config(bg=ON_COLOR)
            else:
                raise Exception()
            self.app.alicat.change_setpoint(setpoint_value=setpt)
        except:
            print("Invalid Setpoint")
            
    def update_setpoint_reading(self):
        flowrate = str.split(self.app.alicat.poll_device_data())[4]
        self.flowrate_label.config(text=f"Flowrate: {flowrate}")
        self.flowrate_label.after(1000, self.update_setpoint_reading)
        
    def change_autoset(self, autoset_temp_var):
        try:
            autoset_temp = int(autoset_temp_var.get())
            duty = self.duty[0]
            if self.autoset_button["bg"] == ON_COLOR or autoset_temp == 0:
                print("Autoset Disabled")
                self.autoset_frame.after_cancel(self.after_id)
                self.autoset_button.config(bg=OFF_COLOR)
                self.heater_buttons[0].config(state=tk.NORMAL)
                self.autoset = False
            elif autoset_temp > 0:
                print("Autoset Enabled")
                self.autoset = True
                self.autoset_button.config(bg=ON_COLOR)
                self.update_autoset(autoset_temp,duty)
                self.heater_buttons[0].config(state=tk.DISABLED)
            else:            
                raise Exception()
        except:
            print("Invalid Autoset")
    
    def update_autoset(self,autoset_temp, duty):
        print("Update")
        current_temp = self.app.temp_controller.read_thermocouples()[0]
        d = tk.StringVar()
        
        if autoset_temp <= current_temp:
            print(f"{current_temp} temp too high, target: {autoset_temp}")
            d.set(int(duty.get())-1)
        elif autoset_temp > current_temp:
            print(f"{current_temp} temp too low, target: {autoset_temp}")
            d.set(duty.get())

        if d.get() != duty.get():
            self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[0],d)
        print(d.get())
        if self.autoset == True:
            self.after_id = self.autoset_frame.after(10000,lambda : self.update_autoset(autoset_temp,duty))
        
