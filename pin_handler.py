import serial
import serial.tools.list_ports
import threading
import os
import datetime
import time
from colorama import Fore

def find_serial_port():
    """Finds the first available serial port."""
    ports = [port.device for port in serial.tools.list_ports.comports()]
    if ports:
        return ports[0]
    else:
        raise ValueError("No serial ports found.")

class PinHandler:
    def __init__(self):
        try:
            self.log_file = self.create_log_file()
            self.ser = serial.Serial(find_serial_port(), 9600)
            self.s = [0]
            # Start a thread to listen for incoming messages
            threading.Thread(target=self.listen_for_messages, daemon=True).start()
        except:
            print(Fore.YELLOW + "Serial port not found! Please check the connection.")
            # Every 5 seconds, attempt to reconnect to the serial port and log if successful
            threading.Thread(target=self.reconnect_to_serial_port, daemon=True).start()

    def reconnect_to_serial_port(self):
        while True:
            try:
                self.ser = serial.Serial(find_serial_port(), 9600)
                print("Serial port reconnected!")
                self.log_message("Serial port reconnected!")
                break
            except:
                print("Serial port not found! Retrying in 5 seconds.")
                self.log_message("Serial port not found! Retrying in 5 seconds.")
                time.sleep(5)

    def create_log_file(self):
        """Creates a log file based on the start time."""
        os.makedirs('logs', exist_ok=True)  # Ensure the logs folder exists
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"logs/log_{timestamp}.txt"
        return log_filename

    def log_message(self, message):
        """Logs a message to the current log file."""
        with open(self.log_file, "a") as log_file:
            log_file.write(message + '\n')

    def unlock_door(self):
        try:
            self.ser.write(b'1')
            return
        except:
            print("Serial port not found! Attempting to reconnect.")
            self.ser = serial.Serial(find_serial_port(), 9600)
            self.ser.write(b'1')
            return

    def lock_door(self):
        try:
            self.ser.write(b'2')
            return
        except:
            print("Serial port not found! Attempting to reconnect.")
            self.ser = serial.Serial(find_serial_port(), 9600)
            self.ser.write(b'2')
            return

    def listen_for_messages(self):
        """Constantly listens for incoming messages and logs them."""
        while True:
            if self.ser.in_waiting > 0:
                incoming_message = self.ser.readline().decode().strip()  # Read incoming message
                self.log_message(incoming_message)  # Log the message
