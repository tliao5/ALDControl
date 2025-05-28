# Constants
BG_COLOR = "grey95"
TEXT_COLOR = "white"
ON_COLOR = "green"
OFF_COLOR = "red4"
BUTTON_STYLE = "raised"
BUTTON_TEXT_COLOR = "grey80"
BORDER_COLOR = "black"
FONT = ("Helvetica", 16)

# Pressure plot default y min and max
Y_MIN_DEFAULT = 0.4
Y_MAX_DEFAULT = 0.8

MAIN_POWER_CHANNEL = "CDAQ1Mod4/line11"
VALVE_CHANNELS = { "AV01": "cDAQ1Mod4/line0", # TMA
                   "AV02": "CDAQ1Mod4/line1", # D20
                   "AV03": "CDAQ1Mod4/line2"} # H20                      
HEATER_CHANNELS = { "h1channel": "CDAQ1Mod4/port0/line5", # heater 1
                          "h2channel": "CDAQ1Mod4/port0/line6", # heater 2
                          "h3channel": "CDAQ1Mod4/port0/line7"} # heater 3
TEMP_CHANNELS = ["ai0", "ai1", "ai2", "ai3", "ai4", "ai5", "ai6"]