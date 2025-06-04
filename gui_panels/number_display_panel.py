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
        self.duty = [d1, d2, d3]

        '''
        self.autoset_frame = tk.Frame(frame,bg=BG_COLOR,pady=10)
        self.autoset_frame.pack(fill=tk.X,padx=10,pady=5)
        autoset_temp=tk.StringVar()
        tk.Label(self.autoset_frame, text ="Autoset Temp", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT,anchor=tk.NW,padx=5,pady=5)
        tk.Entry(self.autoset_frame,width=10,font=FONT,textvariable=autoset_temp).pack(side=tk.LEFT,anchor=tk.NW,padx=5)
        self.autoset_button = tk.Button(self.autoset_frame,text="Autoset",font=FONT,bg=OFF_COLOR,fg=BUTTON_TEXT_COLOR,relief=BUTTON_STYLE,command=lambda:self.change_autoset(autoset_temp))
        self.autoset_button.pack(side=tk.LEFT,padx=5)
        '''

        for i in range(3):
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
        
    '''
    def change_autoset(self, autoset_temp_var):
        
        autoset_temp = int(autoset_temp_var.get())
        duty = self.duty[0]
        if self.setpoint_button["bg"] == ON_COLOR or autoset_temp == 0:
            print("Autoset Disabled")
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
            pass
        #    raise Exception()
        #except:
        #    print("Invalid Autoset")
    
    def update_autoset(self,autoset_temp, duty):
        current_temp = self.app.temp_controller.read_thermocouples()[0]
        if autoset_temp <= current_temp:
            print(f"{current_temp} temp too high, target: {autoset_temp}")
            self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[0],duty)
            print(duty.get())
        elif autoset_temp > current_temp:
            print(f"{current_temp} temp too low, target: {autoset_temp}")
            d = tk.StringVar()
            d.set(int(duty.get())+1)
            self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[0],d)
            print(d.get())
        if self.autoset == True:
            self.autoset_frame.after(10000,lambda : self.update_autoset(autoset_temp,duty))
    '''