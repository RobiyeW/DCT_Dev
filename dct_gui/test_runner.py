import serial
import time

class TestRunner:
    def __init__(self, port='COM3', baudrate=9600, timeout=2):
        """
        Initializes the TestRunner with the specified serial port, baud rate, and timeout.
        :param port: Serial port to connect to (default is 'COM3').
        :param baudrate: Baud rate for the serial connection (default is 9600).
        """
        # Initialize the serial connection parameters
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None

    def connect(self):
        """
        Establishes a serial connection to the specified port.
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            print(f"Connected to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            print(f"Error connecting to {self.port}: {e}")
            self.serial_connection = None

    def disconnect(self):
        """
        Closes the serial connection if it is open.
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print(f"Disconnected from {self.port}.")
        else:
            print("No active connection to disconnect.")
    
    def send_command(self, command):
        """
        Sends a command to the connected device.
        Over Serial connection.

        :param command: Command string to send.
        :return: Response from the device.
        """
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.write((command.strip() + "\n").encode('utf-8'))
                time.sleep(0.1)  # Give the Arduino time to reply
                response = self.serial_connection.read_all().decode('utf-8').strip()
                return response
            except serial.SerialException as e:
                print(f"Error sending command: {e}")
                return None
        else:
            print("No active connection to send commands.")
            return None
    
    def receive_response(self):
        """
        Receives a response from the connected device.
        
        :return: Response string from the device.
        """
        if self.serial_connection and self.serial_connection.is_open:
            try:
                response = self.serial_connection.read_all().decode('utf-8').strip()
                return response
            except serial.SerialException as e:
                print(f"Error receiving response: {e}")
                return None
        else:
            print("No active connection to receive responses.")
            return None