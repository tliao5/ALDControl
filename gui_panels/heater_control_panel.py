import tkinter as tk

## Heater Control Panel
# Interfaces with temp_controller
#   Duty cycle setting
#   Max temperature setting
#   Autoset (Heater 1 only) setting
# Interfaces with Alicat MFC to set gas flowrate

class HeaterControlPanel:
    def __init__(self, app):
        self.app = app
        self.HEATER_CHANNELS = app.HEATER_CHANNELS
        self.BG_COLOR = app.BG_COLOR
        self.BORDER_COLOR = app.BORDER_COLOR
        self.FONT = app.FONT
        self.TEXT_COLOR = app.TEXT_COLOR
        self.BUTTON_TEXT_COLOR = app.BUTTON_TEXT_COLOR
        self.BUTTON_STYLE = app.BUTTON_STYLE
        self.LOG_FILE = app.LOG_FILE
        self.ON_COLOR = app.ON_COLOR
        self.OFF_COLOR = app.OFF_COLOR
        
    def create_heater_control_panel(self):
        frame = tk.Frame(bg=self.BG_COLOR, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        
        self.duty = [tk.StringVar() for i in range(len(self.HEATER_CHANNELS))] # duty entry field variable
        self.max_temp = [tk.StringVar() for i in range(len(self.HEATER_CHANNELS))] # max temp entry field variable
        
        self.heater_buttons = [tk.Button() for i in range(len(self.HEATER_CHANNELS))]
        self.max_temp_buttons = [tk.Button() for i in range(len(self.HEATER_CHANNELS))]
        
        self.heater_buttons = [tk.Button() for i in range(len(self.HEATER_CHANNELS))]
        for i in range(len(self.HEATER_CHANNELS)):
            
            self.duty[i].set(0)
            row = tk.Frame(frame, bg=self.BG_COLOR, pady=10)
            row.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(row, text=f"Heater {i+1}:", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT, padx=5)
            tk.Entry(row, width=4, font=self.FONT, textvariable=self.duty[i]).pack(side=tk.LEFT, padx=5)
            
            # create Heater Buttons
            button = tk.Button(
                row, text="Set", font=self.FONT, bg=self.OFF_COLOR, fg=self.BUTTON_TEXT_COLOR, relief=self.BUTTON_STYLE, width=4,
                command=lambda i=i: self.set_duty_value(i, self.duty[i])
            )
            button.pack(side=tk.LEFT, padx=5)
            self.heater_buttons[i] = button
            
            # create Max Temp Buttons
            tk.Entry(row, width=4, font=self.FONT, textvariable=self.max_temp[i]).pack(side=tk.LEFT, padx=(20,5))
            tk.Label(row, text ="°C", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT,anchor=tk.W,pady=5)
                
            max_temp_button = tk.Button(
                row, text="Max", font=self.FONT, bg=self.OFF_COLOR, fg=self.BUTTON_TEXT_COLOR, relief=self.BUTTON_STYLE,
                command=lambda i=i: self.set_max_temp(i, self.max_temp[i])
            )
            
            max_temp_button.pack(side=tk.LEFT, padx=5)
            self.max_temp_buttons[i] = max_temp_button
            

            # create Autoset Button for Heater 1 only
            if i == 0:
                self.autoset_frame = tk.Frame(row,bg=self.BG_COLOR,pady=10)
                self.autoset_frame.pack(side=tk.RIGHT,padx=5,pady=5)
                autoset_temp=tk.StringVar()
                tk.Entry(self.autoset_frame,width=3,font=self.FONT,textvariable=autoset_temp).pack(side=tk.LEFT,anchor=tk.NW,padx=(5,2),pady=5)
                tk.Label(self.autoset_frame, text ="°C", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT,anchor=tk.NW,pady=5)
                self.autoset_button = tk.Button(self.autoset_frame,text="Autoset",font=self.FONT,bg=self.OFF_COLOR,fg=self.BUTTON_TEXT_COLOR,relief=self.BUTTON_STYLE,command=lambda:self.change_autoset(autoset_temp))
                self.autoset_button.pack(side=tk.LEFT,padx=5)
        
        # create MFC Flowrate button
        mfc = tk.Frame(frame,bg=self.BG_COLOR,pady=10)
        mfc.pack(anchor=tk.N,fill=tk.X,padx=10,pady=5)
        setpt=tk.StringVar()
        tk.Label(mfc, text ="Setpoint: ", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.LEFT,anchor=tk.NW,padx=5,pady=5)
        tk.Entry(mfc,width=5,font=self.FONT,textvariable=setpt).pack(side=tk.LEFT,anchor=tk.NW,padx=5,pady=5)
        self.setpoint_button = tk.Button(mfc,text="Change Setpoint",font=self.FONT,bg=self.OFF_COLOR,fg=self.BUTTON_TEXT_COLOR,relief=self.BUTTON_STYLE,command=lambda:self.change_setpt(setpt))
        self.setpoint_button.pack(side=tk.LEFT,padx=5)
        
        ''' # reading from Alicat the true flowrate - disabled because it caused a lot of latency
        self.flowrate_label = tk.Label(frame,text="Flowrate: ", bg=self.BG_COLOR, font=self.FONT)
        self.flowrate_label.pack(side=tk.TOP,anchor=tk.NW,padx=20,pady=5)
        self.update_setpoint_reading()
        '''   
        # heater key - (displays in reverse order)
        tk.Label(frame, text=f"Heater 4 - Gauges", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 3 - Inlet, TMA", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 2 - Trap", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        tk.Label(frame, text=f"Heater 1 - Chamber", bg=self.BG_COLOR, font=self.FONT).pack(side=tk.BOTTOM, anchor=tk.SW, pady=5,padx=10)
        
        return frame

    # called when Set button is pressed for any heater, sends appropriate call to temp_controller including which thread to update
    def set_duty_value(self, i, duty_cycle_var):
        duty = float(duty_cycle_var.get())
        if self.heater_buttons[i].cget("bg") == self.ON_COLOR or duty==0: # ON -> OFF
            self.app.temp_controller.update_duty_cycle(self.app.temp_controller.queues[i],0)
            self.heater_buttons[i].config(bg=self.OFF_COLOR) # turn button to off if it was on
        elif duty <= 100: # OFF -> ON
            self.heater_buttons[i].config(bg=self.ON_COLOR) 
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
            if max_temp > 0:
                self.app.log_controller.update_max_temp(i,max_temp)
                self.max_temp_buttons[i].config(bg=self.ON_COLOR)
            else:
                self.app.log_controller.update_max_temp(i,300)
                print(f"Max Temp Heater {i+1} set to Default 300")
                self.max_temp_buttons[i].config(bg=self.OFF_COLOR)
        except:
            print(f"Invalid Input. Please enter a positive number") # turn into a console warning
            self.app.log_controller.update_max_temp(i,300)
            print(f"Max Temp Heater {i+1} set to Default 300")
            self.max_temp_buttons[i].config(bg=self.OFF_COLOR)
    
    # Alicat change flowrate set point sccm
    def change_setpt(self,setpt_var):
        try:
            setpt = float(setpt_var.get())
            print(setpt)
            if setpt == 0:
                self.setpoint_button.config(bg=self.OFF_COLOR)
            elif setpt > 0:
                self.setpoint_button.config(bg=self.ON_COLOR)
            else:
                raise Exception()
            self.app.alicat.change_setpoint(setpoint_value=setpt)
        except:
            print("Invalid Setpoint")
            self.setpoint_button.config(bg=self.OFF_COLOR)
    
    
    def change_autoset(self, autoset_temp_var):
        try:
            self.autoset_temp = float(autoset_temp_var.get())
            duty = self.duty[0]
            if self.autoset_button["bg"] == self.ON_COLOR or self.autoset_temp == 0:
                print("Autoset Disabled")
                self.autoset_button.config(bg=self.OFF_COLOR)
                self.heater_buttons[0].config(state=tk.NORMAL) # re-disable Set button for Heater 1
                self.app.temp_controller.autoset.clear()
            elif self.autoset_temp > 0:
                print("Autoset Enabled")
                self.autoset_button.config(bg=self.ON_COLOR)
                self.heater_buttons[0].config(state=tk.DISABLED) # disable Set button for Heater 1 when autoset is active
                self.app.temp_controller.autoset.set()
                self.app.temp_controller.autoset_queue.put(self.autoset_temp)
        except:
            print("Invalid input")
            self.autoset_button.config(bg=self.OFF_COLOR)
            self.heater_buttons[0].config(state=tk.NORMAL)
            self.app.temp_controller.autoset.clear()
            
    
    # placeholder if this panel ever has something that needs cleanup
    def close(self):
        pass

