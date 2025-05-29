import serial
import time
 
class AlicatController:
    def __init__(self, port, baudrate=19200, timeout=0.2):
        """
        Initialize the Alicat serial communication.
        :param port: COM port (Windows: 'COMX', Linux/Mac: '/dev/ttyUSBX')
        :param baudrate: Baud rate of the device (default: 19200)
        :param timeout: Read timeout in seconds
        """
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2)  # initialize the serial connection
 
    def send_command(self, command):
        """
        Send a command to the Alicat device.
        :param command: Alicat command string
        """
        if not self.ser.is_open:
            self.ser.open()
        self.ser.write((command + '\r').encode())  # Alicat expects carriage return
        time.sleep(0.1)
        response = self.ser.readline().decode().strip()
        return response
 
    def poll_device_data(self, unit_id='A'):
        """
        Poll the Alicat device for current measurements.
        :param unit_id: The Unit ID of the device (default: 'A')
        :return: Response data
        """
        return self.send_command(unit_id)
 
    def set_gas(self, unit_id='A', gas_number=1):
        """
        Change the gas type the device is measuring.
        :param unit_id: The Unit ID of the device (default: 'A')
        :param gas_number: The gas number from the device's available gases list
        """
        return self.send_command(f"{unit_id}G{gas_number}")
 
    def change_setpoint(self, unit_id='A', setpoint_value=0.0):
        """
        Set a new flow or pressure setpoint.
        :param unit_id: The Unit ID of the device (default: 'A')
        :param setpoint_value: The new setpoint value
        """
        return self.send_command(f"{unit_id}S{setpoint_value}")
 
    def tare_flow(self, unit_id='A'):
        """
        Perform a tare operation for flow measurement.
        :param unit_id: The Unit ID of the device (default: 'A')
        """
        return self.send_command(f"{unit_id}V")
 
    def tare_pressure(self, unit_id='A'):
        """
        Perform a tare operation for pressure measurement.
        :param unit_id: The Unit ID of the device (default: 'A')
        """
        return self.send_command(f"{unit_id}P")
 
    def get_firmware_version(self, unit_id='A'):
        """
        Get the firmware version of the device.
        :param unit_id: The Unit ID of the device (default: 'A')
        """
        return self.send_command(f"{unit_id}VE")
 
    def close(self):
        """
        Close the serial connection.
        """
        if self.ser.is_open:
            self.ser.close()
            
 
if __name__ == "__main__":
    alicat = AlicatController(port="COM6")
    #alicat.send_command("@B")
    #print("serial lines:", alicat.ser.readline())
    #print("Polling Data:", str.split(alicat.poll_device_data(unit_id='A')))
    #print("Setting Setpoint to 10.0:", alicat.change_setpoint(setpoint_value=0.0))
 
    alicat.close()