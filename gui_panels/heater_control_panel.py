import tkinter as tk
from config import *

## Heater Control Panel
# Interfaces with temp_controller
#   Duty cycle setting
#   Max temperature setting
#   Autoset (Heater 1 only) setting
# Interfaces with Alicat MFC to set gas flowrate

class HeaterControlPanel:
    def __init__(self, app):
        self.app = app
        
    def create_heater_control_panel(self):
        frame = tk.Frame(bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        
        self.duty = [tk.StringVar() for i in range(len(HEATER_CHANNELS))] # duty entry field variable
        self.max_temp = [tk.StringVar() for i in range(len(HEATER_CHANNELS))] # max temp entry field variable
        
        self.heater_buttons = [tk.Button() for i in range(len(HEATER_CHANNELS))]
        self.max_temp_buttons = [tk.Button() for i in range(len(HEATER_CHANNELS))]
        
        self.heater_buttons = [tk.Button() for i in range(len(HEATER_CHANNELS))]
        for i in range(len(HEATER_CHANNELS)):
            
            self.duty[i].set(0)
            row = tk.Frame(frame, bg=BG_COLOR, pady=10)
            row.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(row, text=f"Heater {i+1}:", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT, padx=5)
            tk.Entry(row, width=4, font=FONT, textvariable=self.duty[i]).pack(side=tk.LEFT, padx=5)
            
            # create Heater Buttons
            button = tk.Button(
                row, text="Set", font=FONT, bg=OFF_COLOR, fg=BUTTON_TEXT_COLOR, relief=BUTTON_STYLE, width=4,
                command=lambda i=i: self.set_duty_value(i, self.duty[i])
            )
            button.pack(side=tk.LEFT, padx=5)
            self.heater_buttons[i] = button
            
            # create Max Temp Buttons
            tk.Entry(row, width=4, font=FONT, textvariable=self.max_temp[i]).pack(side=tk.LEFT, padx=(20,5))
            tk.Label(row, text ="°C", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT,anchor=tk.W,pady=5)
                
            max_temp_button = tk.Button(
                row, text="Max", font=FONT, bg=OFF_COLOR, fg=BUTTON_TEXT_COLOR, relief=BUTTON_STYLE,
                command=lambda i=i: self.set_max_temp(i, self.max_temp[i])
            )
            
            max_temp_button.pack(side=tk.LEFT, padx=5)
            self.max_temp_buttons[i] = max_temp_button
            

            # create Autoset Button for Heater 1 only
            if i == 0:
                self.autoset_frame = tk.Frame(row,bg=BG_COLOR,pady=10)
                self.autoset_frame.pack(side=tk.RIGHT,padx=5,pady=5)
                autoset_temp=tk.StringVar()
                tk.Entry(self.autoset_frame,width=3,font=FONT,textvariable=autoset_temp).pack(side=tk.LEFT,anchor=tk.NW,padx=(5,2),pady=5)
                tk.Label(self.autoset_frame, text ="°C", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT,anchor=tk.NW,pady=5)
                self.autoset_button = tk.Button(self.autoset_frame,text="Autoset",font=FONT,bg=OFF_COLOR,fg=BUTTON_TEXT_COLOR,relief=BUTTON_STYLE,command=lambda:self.change_autoset(autoset_temp))
                self.autoset_button.pack(side=tk.LEFT,padx=5)
        
        # create MFC Flowrate button
        mfc = tk.Frame(frame,bg=BG_COLOR,pady=10)
        mfc.pack(anchor=tk.N,fill=tk.X,padx=10,pady=5)
        setpt=tk.StringVar()
        tk.Label(mfc, text ="Setpoint: ", bg=BG_COLOR, font=FONT).pack(side=tk.LEFT,anchor=tk.NW,padx=5,pady=5)
        tk.Entry(mfc,width=5,font=FONT,textvariable=setpt).pack(side=tk.LEFT,anchor=tk.NW,padx=5,pady=5)
        self.setpoint_button = tk.Button(mfc,text="Change Setpoint",font=FONT,bg=OFF_COLOR,fg=BUTTON_TEXT_COLOR,relief=BUTTON_STYLE,command=lambda:self.change_setpt(setpt))
        self.setpoint_button.pack(side=tk.LEFT,padx=5)
        
        ''' # reading from Alicat the true flowrate - disabled because it caused a lot of latency
        self.flowrate_label = tk.Label(frame,text="Flowrate: ", bg=BG_COLOR, font=FONT)
        self.flowrate_label.pack(side=tk.TOP,anchor=tk.NW,padx=20,pady=5)
        self.update_setpoint_reading()
        '''   
        # heater key - (displays in reverse order)
        tk.Label(frame, text=f"Heater 4 - Gauges", bg=BG_COLOR, font=FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 3 - Inlet, TMA", bg=BG_COLOR, font=FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 2 - Trap", bg=BG_COLOR, font=FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 1 - Chamber", bg=BG_COLOR, font=FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        
        return frame

    # called when Set button is pressed for any heater, sends appropriate call to temp_controller including which thread to update
    """def set_duty_value(self, i, duty_cycle_var):
        try:
            duty = float(duty_cycle_var.get())
            self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[i],duty)
            if duty = 0: # update set button color if heater is active or not
                self.heater_buttons[i].config(bg=OFF_COLOR)
            else:
                self.heater_buttons[i].config(bg=ON_COLOR)
                print(f"Heater {i+1} set to {duty}%")
        except:
            print(f"Invalid Input. Please enter an integer between 0 and {self.app.temp_controller.ticks_per_cycle}.") # turn into a console warning
            self.heater_buttons[i].config(bg=OFF_COLOR)"""
    def set_duty_value(self, i, duty_cycle_var):
        duty = float(duty_cycle_var.get())
        if self.heater_buttons[i].cget("bg") == ON_COLOR or duty==0: # ON -> OFF
            self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[i],0)
            self.heater_buttons[i].config(bg=OFF_COLOR) # turn button to off if it was on
        elif duty <= 100: # OFF -> ON
            self.heater_buttons[i].config(bg=ON_COLOR) 
            self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[i],duty)
            print(f"Heater {i+1} set to {duty}%")
        #except:
            #print(f"Invalid Input. Please enter an integer between 0 and {self.app.temp_controller.ticks_per_cycle}.") # turn into a console warning
            #self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[i],0)
            #self.heater_buttons[i].config(bg=OFF_COLOR)

    # called when Max button is pressed for any heater, updates log_controller which contains temperature watchdog logic
    def set_max_temp(self, i, max_temp_var):
        try:
            max_temp = float(max_temp_var.get())
            self.app.log_controller.update_max_temp(i,max_temp)
            if max_temp > 0:
                self.max_temp_buttons[i].config(bg=ON_COLOR)
            else:
                self.max_temp_buttons[i].config(bg=OFF_COLOR)
        except:
            print(f"Invalid Input. Please enter a positive number") # turn into a console warning
            self.heater_buttons[i].config(bg=OFF_COLOR)
    
    # Alicat change flowrate set point sccm
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
            self.setpoint_button.config(bg=OFF_COLOR)
    
    
    def change_autoset(self, autoset_temp_var):
        try:
            self.autoset_temp = float(autoset_temp_var.get())
            duty = self.duty[0]
            if self.autoset_button["bg"] == ON_COLOR or self.autoset_temp == 0:
                print("Autoset Disabled")
                self.autoset_button.config(bg=OFF_COLOR)
                self.heater_buttons[0].config(state=tk.NORMAL) # re-disable Set button for Heater 1
                self.app.temp_controller.autoset.clear()
            elif self.autoset_temp > 0:
                print("Autoset Enabled")
                self.autoset_button.config(bg=ON_COLOR)
                self.heater_buttons[0].config(state=tk.DISABLED) # disable Set button for Heater 1 when autoset is active
                self.app.temp_controller.autoset.set()
                self.app.temp_controller.autoset_queue.put(self.autoset_temp)
        except:
            print("Invalid input")
            self.autoset_button.config(bg=OFF_COLOR)
            self.heater_buttons[0].config(state=tk.NORMAL)
            self.app.temp_controller.autoset.clear()
            
    
    # placeholder if this panel ever has something that needs cleanup
    def close(self):
        pass
