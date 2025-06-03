# ALDControl  
ALD Control System Overview – Tyler Liao  
The ALD Control software controls these aspects of the ALD Reactor  
╚ Via NI DAQ  
   └ Thermocouples – Temperature Reading  
   └ MKS Baratron – Pressure Reading  
   └ Band Heaters – System Temperature Control  
   └ Swagelok ALD Valves – Run Cycle Control  
   └ Alicat Mass Flow Controller – Carrier Gas Flow  
  
The control application uses Python’s Tkinter package and consists of the below component  
+==========================================================================================+  
| app.py – The main program loop, also initializes of all controllers and GUI Panels                            |  
| ╚ controllers	================= control different aspects of the reactor, using nidaqmx functionality         |  
|   └ ald_controller -----------– ALD Run cycle logic, creates new thread at run start                          |  
|   └ mfc_reader ---------------– Alicat flow control interface													                        |  
|   └ pressure_controller ------– pressure reading from MKS Baratron											                      |  
|   └ temp_controller ----------– temperature reading from thermocouples, creates 3 threads to control heaters.	|  
|   └ valve_controller ---------– logic to open, close, and pulse valves										                    |  
| ╚ gui_panel =================== allow the user to interface with the controllers								              |  
|   └ main_power ---------------- button that turns on and off the main power relay								              |  
|   └ ald_panel ----------------- run start controls															                              |  
|   └ manual_control_panel -----– manual ALD valve control and file loading										                  |   
|   └ number_display_panel -----– heater and mass flow control													                        |  
|   └ plot_panel ----------------  real time display of pressures and temperatures								              |  
+===============================================================================================================+  
  
  
How to start a run:
1. Doublecheck config file to make sure log file, etc. are correct
2. Run app.py in command line
3. Press the "Main Power" button at the top to turn on heater and valve controls
4. Set duty values to each heater to heat up system (turn on variac - soon to be replaced by another nidaqmx controlled heater band)
5. Press the "Load File" button and select the recipe file
6. Review the recipe file
7. Enter the number of cycles into the "Loops" field
8. Press "Confirm" to begin the ALD run

Notes:
- Currently logging is done at each update call of the animate() function from plot_panel

- There are two timers that are active during a run, the main thread elapsed_time, and the aldRun thread's elapsed time, I force them to sync, but may update how this is arranged in the future

- app.py runs in the main thread
    - aldRun ------ main run thread
    - h1dutycycle - controls heater 1 duty cycle
    - h2dutycycle - controls heater 1 duty cycle
    - h3dutycycle - controls heater 1 duty cycle
-  .after() events: consistent updates to other parts of the system using tkinter's built in event queue .after() function
    - ald_panel.update_progress_bar() - calls every "900ms" but likely a bit slower due to latency, ticks down main thread run timer
    - number_display_panel.update_setpoint_reading(self) - calls ever "1000ms", could probably be less frequent

- All threads and tasks should close automatically when the program is closed, but may take some time

Planned Features:
- Automatic temperature adjustment to fine tune accuracy of duty cycle temperature control
- Pause Run feature, allowing adjustments to be made mid-run
- Performance increases? look into smoothness of display, currently pretty laggy

===================Function and Class Overview==============

app.py - main program
-run main program
-setup logging using Python logging module
-initializes all controllers
-initializes all panels
    - outer_frame = tk.Frame() used for the main box

    tk.PanedWindow() allows the widows to be resized dynamically inside the gui
    - top_pane - holds top_frame which contains the main power button
    - main_pane - center content window
    - horizontal_pane - divides the center content window into left and right
    - bottom_pane - holds the manual control panel and the ALD run control panel
-closing logic
    - calls the close function from each component, making sure all NI DAQ tasks and threads are closed


Controllers:
ald_controller() ALD Run cycle logic
    - initializes self.stopthread = threading.Event(), used to close the recipe thread
    - initializes self.queue = queue.Queue(), manages passing data to and from the thread
     
    - create_run_thread(self, loops, vc) starts a new thread running the aldRun() function
    	- loops = number of ALD cycles specified by user
    	- vc = valve_controller object 
    
    - aldRun(self,loops,vc,queue) pulses valves at time specified by recipe file
    	- loops = number of ALD cycles specified by user
	- vc = valve_controller object
	- queue = ald_controller's queue, right now used to pass elapsed time
	
	- accesses recipe file stored in ald_controller.file
	- for i in range(loops) -------------------- based on number of cycles
		- for j in range(0,len(dataNP),1) -- goes down columns in recipe, dataNP
			loop logic:
			- exits early if stopthread is triggered
			
			- otherwise, reads the current row to see which valves to trigger
			- store the index of each triggered valve
			
			- if there are valves to pulse, call pulse_valve()
			- if no valves found, instead wait and purge
			
			- add up time of each cycle, send elapsed_time back through queue


mfc_reader(self, port) Alicat Controller, we only use some of its functions
    - initialize Alicat serial communication
    
    - send_command(self, command)
    	- used by other functions to send a command to the Alicat 

    - poll_device_data(self,unit_id='A')
	- returns a string of device readings, we use this to extract flowrate 

    - change_setpoint(self,unit_id='A',setpoint_value=0.0)
	- changes setpoint to new value

pressure_controller
    - initializes nidaqmx task for MKS Baratron

    -  read_pressure(self)
	- reads voltage, convert to torr 

    - readPressure_pdr2000(self)
    	- unused

    - close(self)
	- closes nidaqmx task 

temp_controller
    - initializes Heater nidaqmx tasks and Thermocouple nidaqmx tasks
    - initializes queue for communication with heater threads
    - initializes heater threads

    - create_heater_queue(self)
	- returns list of queues for temp_controller.queues[:]
    - create_heater_tasks(self)
    	- returns a list of taks for temp_controller.tasks[:]
    - start_threads(self)
	- returns duty cycle threads, one for each heater
    - create_thermocouple_tasks(self)
	- sets up thermocouple channels
	- returns task for thermocouples

    - read_thermocouples(self)
	- returns a string containing readings from all thermocouples

    - duty_cycle(self,stopthread,duty_queue,task,tps) runs duty cycle
	- while loop, check if stopthread is set to stop cycle
	- otherwise, check if duty_queue has a new value
		- update duty value
	- check if voltage should be on or off based on cycle timing, sleep, repeat
	- after loop, shut down nidaqmx task

    - update_duty_cycle(self,queue,duty)
	- check if duty cycle value is valid
		- send updated duty to specified thread

    - close(self)
	- join all threads, close thermocouple nidaqmx task

valve_controller
    - initialize create valve tasks

    - create_valve_tasks(self)
	- returns 3 tasks, one for each heater 
    
    - open_valve(self, task)
    	- opens specified valve, sleeps for 0.1s to make sure valve has time to open

    - close_valve(self,task)
	- closes specified valve, sleeps for 0.1s to make sure valve has time to open

    - pulse_valve(self,indicies,pulse_length)
	- indicies refers to the index in the task array of the valve(s) to be pulsed 
	- pulses valve for length pulse_length
	- intended to support multiple valves pulsing simultaneously, need to add support for different pulse_lengths by valve

    - close_all(self)
	- closes all valves, used at end of program and before closing software to make sure all valves are shut

    - close(self)
	- closes all valve tasks


GUI Panels
ald_panel
    - initializes blank variables and creates panels
    
    - create_ald_panel(self,parent) called during app startup to generate panel
	- creates loops entry field and run button
	- creates progress bar
	- displays what log file is listed in config

    - start_run(self)
	- called when Run Recipe button is press, prompts confirmation
	- calculate run time for progress bar display
    
    - confirm_run(self,loops)
	- disables all other panel buttons, including manual panel buttons until run is over
	- actually starts the loop by calling create_run_thread() from ald_controller
    
    - update_progress_bar(self)
	- tracks progress on the GUI side, (the real run time is controlled from the aldRun thread)
	- kind of a hacky solution, polls the elapsed_time from the aldRun to make sure they stay synced
	- On run finish, 
		- calls enable_manual_controls()
	 	- reenables ald_panel buttons

    - format_time(self,seconds)
	- utility function returns a string converting seconds to HH:MM:SS time format

    - disable_manual_controls(self)
    - enable_manual_controls(self)
	

main_power
    - initializes by calling create_main_power_task()

    - create_main_power_task(self)
	- creates nidaqmx task for main power relay

    - create_main_power_button(self,parent)
	- called during app startup
	- creates main power button, default off

    - toggle_main_power(self)
	- called when main_power_button is pressed
	- uses main_power_button text and color to track whether or not power is on or off
	- toggles to other state

    - close(self)
	- turns off main power
	- closes main power task

manual_control_panel
    - initializes default variables
    
    - create_manual_controls(self,parent)
    	- called during app startup
	
	- creates buttons to open the manual control window and load files

    - load_file(self)
	- asks user to select file
	- gets file title, updates file reference in ALD Controller
	- calls displa_csv(file_path)

    - display_csv(file_path)
	- clears old csv panel
	- opens file
	- loop row by row, filling in values

    - open_manual_control(self)
	- creates a new subwindow using tk.Toplevel
	- allows manual opening, closing, and pulsing of valve using valve_controller commands


number_display_panel
    - initializes blank heater_buttons

    - create_number_display_panel(self)
    	- self.duty - list of duty cycle entry fields
    	- creates heater buttons which send value from the entry field to set_duty_value()
	- display text key for which heater corresponds to what part of the system
    	- set_duty_value(self,i,duty_cycle_var)
		- i = which heater button this is, corresponding to the duty cycle thread to be targetted
		- duty_cycle_var = tk.Stringvar() from the entry field
		- updates color to show whether or not heater is active, updates duty value by calling update_duty_cycle()

    - to be added: temperature automatic adjustment

plot_panel
    - initializes plot and sensors, - eventually update to call values from config

    - plot_initialize(self)
	- creates plot with default values
	- creates deque() for pressure and time in order to display
	- deque set to automatically limit the number of values saved to be displayed

    - animate(self,i)
	- call data from thermocouples and pressure reading, update deque-s
	- log data to log file
	- update y-axis size
	- clear old plot
	- create new plot using deque-s
	- display thermocouple readings in a list
		- position automatically scaled based on y-axis size

    - close(self)
	- close plot
