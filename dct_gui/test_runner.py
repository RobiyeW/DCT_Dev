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
            self.serial_connection.flushInput()
            print(f"Connected to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            print(f"Error connecting to {self.port}: {e}")
            self.serial_connection = None

    def is_connected(self):
        """
        Checks if the serial connection is open.
        
        :return: True if connected, False otherwise.
        """
        return self.serial_connection is not None and self.serial_connection.is_open
    
    def __del__(self):
        """
        Destructor to ensure the serial connection is closed when the object is deleted.
        """
        try:
            self.close_connection()
        except Exception:
            pass  # Avoid exceptions during garbage collection
            
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
    
    def receive_response(self, timeout=2):
        """
        Receives a response from the connected device.
        
        :return: Response string from the device.
        """
        if self.serial_connection and self.serial_connection.is_open:
            start_time = time.time()
            response = ""
            try:
                while time.time() - start_time < timeout:
                    if self.serial_connection.in_waiting > 0:
                        # Read all available bytes
                        response += self.serial_connection.read_all().decode('utf-8')
                    time.sleep(0.1)
                return response.strip()
            except serial.SerialException as e:
                print(f"Error receiving response: {e}")
                return None
        else:
            print("No active connection to receive responses.")
            return None
    
    def close_connection(self):
        """
        Closes the serial connection if it is open.
        """

        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                print(f"Connection to {self.port} closed.")
            except serial.SerialException as e:
                print(f"Error while closing connection: {e}")
        else:
            print("No active connection to close.")
