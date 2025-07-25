# ALDControl
## ALD Control System Overview
The ALD Control software manages various aspects of the ALD Reactor, including temperature, pressure, valve operations, and carrier gas flow. It integrates hardware control via NI DAQ and Alicat Mass Flow Controller, and provides a graphical interface built with Python's tkinter package.

**Hardware Integration**

╚ Via NI DAQ 
   └ Thermocouples – Temperature Reading 
   └ MKS Baratron – Pressure Reading 
   └ Band Heaters – System Temperature Control 
   └ Swagelok ALD Valves – Run Cycle Control 
╚ Alicat Mass Flow Controller – Carrier Gas Flow 

## Software Components
The control application consists of the following components:

**app.py** – The main program loop, initializes all controllers and GUI panels

**config.py** - System configuration and visual style 

╚ **controllers** ================== Controls different aspects of the reactor using nidaqmx functionality  
   └ *ald_controller* -----------– ALD run cycle logic, creates new thread at run start  
   └ *mfc_reader* ---------------– Alicat flow control interface  
   └ *pressure_controller* ------– Pressure reading from MKS Baratron  
   └ *temp_controller* ----------– Temperature reading from thermocouples, creates threads to control heaters  
   └ *valve_controller* ---------– Logic to open, close, and pulse valves  
╚ **gui_panel** =================== Allows the user to interface with the controllers   
   └ *main_power* ---------------- Button that turns on and off the main power relay  
   └ *ald_panel* ----------------- Run start controls  
   └ *manual_control_panel* -----– Manual ALD valve control and file loading  
   └ *heater_control_panel* -----– Heater and mass flow control  
   └ *plot_panel* ---------------- Real-time display of pressures and temperatures  


# How to Start a Run

1. Double-check the `config.py` file to ensure log file paths and other settings are correct.
2. Run `app.py` in the command line.
3. Press the **Main Power** button at the top to enable heater and valve controls.
4. Set duty values for each heater to heat up the system.
5. Set appropriate max temperatures for each component
6. Wait until desired temperatures are reached (Use **Show Temperatures** button to display temperature curves)
7. Press the **Load File** button and select the recipe file.
8. Review the recipe file displayed in the GUI.
9. Enter the number of cycles into the **Cycles** field.
10. Press **Confirm** to begin the ALD run.

# Notes
## Logging/Plotting:

- Logging occurs every 0.5s when the log_controller gathers data and log records from various parts of the program

- The main plot shows Pressure vs. Samples, not quite Pressure vs. Time

## Timers:
- Two timers are active during a run: the main thread's elapsed time and the aldRun thread's elapsed time. These are synchronized manually but may be updated in the future.

## Threads:
- app.py is the main thread
- Additional threads include:
    - ALD run thread (ald_controller)
    - Heater duty cycle threads (temp_controller)
    - Logging thread (log_controller)
- Thread communicate mostly via python queue.Queue() objects
- All threads and tasks should close automatically when the program is terminated, but this may take some time. Often the window will show "Not Responding" while waiting for a particular thread to close
    
## Tkinter .after() Events:
- ald_panel.update_progress_bar()
- Updates every ~900ms to control the run timer in the main thread.        

## Planned Features:
- Performance improvements to enhance display smoothness and reduce latency
- "De-spaghettification" of various controllers for an easier modification process
    
# Function and Class Overview
---

## `app.py` – Main Program

### **Purpose**  
- Runs the main program loop.  
- Sets up logging using Python's logging module.  
- Initializes all controllers and GUI panels.  

### **Structure**  
- `outer_frame` – Main container for the GUI.  
- `tk.PanedWindow()` – Allows dynamic resizing of GUI panels.  

### **Panels**  
- `top_pane` – Contains the main power button.  
- `main_pane` – Center content window.  
- `horizontal_pane` – Divides the center content window into left and right sections.  
- `bottom_pane` – Contains the manual control panel and ALD run control panel.  

### **Closing Logic**  
- Calls the `close()` function for each component to ensure all NI DAQ tasks and threads are properly terminated.  

---

## `config.py` - Configuration File

This config defines the constants and configuration settings used throughout the ALD reactor control program. These constants include visual style for the GUI, log file paths, hardware channels, and operational parameters for the system's components.

### Key Features

#### GUI Styling
- Defines colors, fonts, and button styles for the graphical user interface.

#### Logging Configuration
- Specifies file paths for application logs (`PressureTempJuly.log`) and monitoring logs (`monitor.log`).

#### Hardware Channel Mappings
- Maps control channels for main power, valves, heaters, temperature sensors, and pressure sensors to specific hardware ports.

#### Operational Parameters
- Sets default values for pressure plot limits (`Y_MIN_DEFAULT` and `Y_MAX_DEFAULT`).
- Configures duty cycle length for heater operations.

#### Sensor and Port Settings
- Lists temperature sensor channels and their corresponding names.
- Defines the communication port for the mass flow controller (`MFC_PORT`).

---

## Controllers

### `ald_controller.py` – ALD Recipe Controller

#### **Purpose**  
- Manages the execution of ALD recipes by creating a dedicated thread for running the recipe.  
- Interfaces with the `valve_controller` to control valve operations.  
- Communicates with the `ald_panel` for pausing and progress tracking.  

#### **Key Functions**  
- `create_run_thread(loops, vc)` – Starts a new thread to execute the ALD recipe.  
- `aldRun(loops, vc, queue)` – Executes the recipe by pulsing valves based on the recipe file. Handles multiple loops and complex valve operations. Updates elapsed time for progress tracking.  
- `close()` – Safely stops the thread and ensures all valves are closed.  

---

### `alicat_controller.py` – Alicat Mass Flow Controller (MFC) Interface

#### **Purpose**  
- Provides an interface for communicating with the Alicat MFC via serial communication.  
- Manages gas flowrate and pressure settings.  

#### **Key Functions**  
- `send_command(command)` – Sends commands to the Alicat device.  
- `change_setpoint(unit_id, setpoint_value)` – Sets a new flowrate or pressure setpoint.  
- `poll_device_data(unit_id)` – Retrieves current measurements from the device.  
- `close()` – Closes the serial connection.  

---

### `pressure_controller.py` – Pressure Controller

#### **Purpose**  
- Interfaces with the MKS Baratron pressure sensor using `nidaqmx`.  
- Reads and converts voltage data to pressure values.  

#### **Key Functions**  
- `read_pressure()` – Reads pressure data and converts it to Torr.  
- `close()` – Closes the `nidaqmx` task.  

---

### `temp_controller.py` – Temperature Controller

#### **Purpose**  
- Manages heaters and thermocouples in the reactor.  
- Supports dynamic duty cycles and autoset functionality for Heater 1.  

#### **Key Functions**  
- `create_heater_tasks()` – Initializes `nidaqmx` tasks for heaters.  
- `create_thermocouple_tasks()` – Configures `nidaqmx` tasks for thermocouples.  
- `start_threads()` – Starts threads for heater duty cycles.  
- `autoset_duty_cycle()` – Dynamically adjusts Heater 1's duty cycle based on temperature.  
- `close()` – Safely stops threads and closes all tasks.  

---

### `valve_controller.py` – Valve Controller

#### **Purpose**  
- Manages the operation of valves in the reactor.  
- Provides methods to open, close, pulse, and close all valves.  

#### **Key Functions**  
- `create_valve_tasks()` – Initializes `nidaqmx` tasks for valves.  
- `open_valve(task)` – Opens a specific valve.  
- `close_valve(task)` – Closes a specific valve.  
- `pulse_valve(indices, pulse_length)` – Temporarily opens valves for a specified duration.  
- `close_all()` – Closes all valves.  
- `close()` – Releases all `nidaqmx` resources.  

---

## GUI Panels

### `ald_panel.py` – ALD Panel

#### **Purpose**  
- Provides controls for starting, pausing, and monitoring ALD runs.  

#### **Key Functions**  
- `create_ald_panel(parent)` – Creates the panel with input fields, buttons, and a progress bar.  
- `start_run()` – Prepares the run by validating input and calculating runtime.  
- `confirm_run(loops)` – Starts the ALD run and disables other controls.  
- `update_progress_bar()` – Tracks and displays run progress.  

---

### `main_power.py` – Main Power Control

#### **Purpose**  
- Manages the main power relay for the reactor.  

#### **Key Functions**  
- `create_main_power_task()` – Initializes the `nidaqmx` task for the power relay.  
- `toggle_main_power()` – Toggles the power state (ON/OFF).  
- `close()` – Ensures the relay is turned off and the task is closed.  

---

### `manual_control_panel.py` – Manual Control Panel

#### **Purpose**  
- Allows users to load recipe files and manually control valves.  

#### **Key Functions**  
- `load_file()` – Loads a recipe file and updates the `ald_controller`.  
- `open_manual_control()` – Opens a sub-panel for manual valve operations.  

---

### `heater_control_panel.py` – Heater Control Panel

#### **Purpose**  
- Provides controls for managing heater duty cycles, maximum temperature settings, and gas flowrates.  
- Interfaces with the `temp_controller` for heater operations and the Alicat MFC for flowrate adjustments.  

#### **Key Functions**  
- `create_heater_control_panel()` – Creates entry fields and buttons for heater and flowrate controls.  
- `set_duty_value(i, duty_cycle_var)` – Updates the duty cycle for a specific heater.  
- `set_max_temp(i, max_temp_var)` – Sets the maximum temperature limit for a specific heater.  
- `change_setpt(setpt_var)` – Updates the Alicat MFC flowrate setpoint.  
- `change_autoset(autoset_temp_var)` – Enables or disables autoset functionality for Heater 1.  

---

### `plot_panel.py` – Plot Panel

#### **Purpose**  
- Provides real-time monitoring of pressure and temperature data using `matplotlib`.  
- Integrates with the `log_controller` to retrieve and display data dynamically.  

#### **Key Functions**  
- `plot_initialize()` – Sets up the plot with default settings.  
- `animate(i)` – Updates the plot with real-time data from pressure and temperature sensors.  
- `toggle_show_temperatures()` – Toggles the visibility of temperature data on the plot.  
- `close()` – Ensures proper cleanup of `matplotlib` resources.  

---

### `log_controller.py` – Log Controller

#### **Purpose**  
- Manages data logging, real-time monitoring, and safety mechanisms for the reactor.  
- Monitors temperature thresholds to prevent overheating and triggers safety measures when necessary.  

#### **Key Functions**  
- `record_data()` – Collects sensor data and logs it to the main and monitor log files.  
- `update_max_temp(i, max_temp)` – Updates the maximum temperature threshold for a specific sensor.  
- `kill_run()` – Pauses the ALD run and disables main power during overheating events.  
- `close()` – Safely stops the logging thread and releases resources.  

---

# **Python Libraries**  
- **`tkinter`** – Used for building the graphical user interface.  
- **`matplotlib`** – Used for real-time plotting of pressure and temperature data.  
- **`nidaqmx`** – Used for interfacing with NI DAQ hardware for sensor and actuator control.  
- **`serial`** – Used for communicating with the Alicat Mass Flow Controller.  
- **`logging`** – Used for logging events and data for monitoring and debugging.
- **`queue`** - Used for managing thread communication
- **`collections.deque`** - Used to store temperature and pressure data in a threadsafe manner

---
