# Constants
BG_COLOR = "grey95"
TEXT_COLOR = "white"
ON_COLOR = "green"
OFF_COLOR = "red4"
BUTTON_STYLE = "raised"
BUTTON_TEXT_COLOR = "grey85"
BORDER_COLOR = "black"
FONT = ("Helvetica", 22)


# Log output
LOG_FILE = "PressureTempJuly.log"
MONITOR_LOG_FILE = "monitor.log"

# Pressure plot default y min and max
Y_MIN_DEFAULT = 0.575
Y_MAX_DEFAULT = 0.610



MAIN_POWER_CHANNEL = "CDAQ1Mod4/line11"

VALVE_CHANNELS = { "AV01": "cDAQ1Mod4/line0", # TMA
                   "AV02": "CDAQ1Mod4/line1", # D20
                   "AV03": "CDAQ1Mod4/line2"} # H20      
                   
HEATER_CHANNELS = { "h1channel": "CDAQ1Mod4/port0/line5", # heater 1
                    "h2channel": "CDAQ1Mod4/port0/line6", # heater 2
                    "h3channel": "CDAQ1Mod4/port0/line7", # heater 3
                    "h4channel": "CDAQ1Mod4/port0/line8"} # heater 4
DUTY_CYCLE_LENGTH = 10 # seconds

TEMP_CHANNELS = ["ai0", "ai1", "ai2", "ai3", "ai4", "ai5", "ai6"]
SENSOR_NAMES = ["main reactor", "inlet lower", "inlet upper", "exhaust", "TMA", "Trap", "Gauges","Pressure"]


PRESSURE_CHANNEL = {"Pchannel":"cDAQ1Mod2/ai2"}

MFC_PORT = "COM6"
