import os
import datetime

class LogHandler():
    def __init__(self):
        self.log_file = self.create_log_file()

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