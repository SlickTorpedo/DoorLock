#This is only used if you have a light controller that you want to use.
#You can checkout the repo for the light controller at
#https://github.com/SlickTorpedo/LightController
import requests
import os
from dotenv import load_dotenv

import pytz
from datetime import datetime

load_dotenv()

class LightControllerHook:
    def __init__(self):
        self.url = os.getenv("LIGHT_CONTROLLER_URL")
        self.auth_token = os.getenv("LIGHT_CONTROLLER_AUTH_TOKEN")

    def _send_command(self, state, discriminator):
        valid_states = ["on","off"]
        if state not in valid_states:
            return "Invalid state, must be either 'on' or 'off'"
        
        valid_discriminators = ['left', 'right', 'both']
        if discriminator not in valid_discriminators:
            return "Invalid discriminator, must be either 'left', 'right', or 'both'"

        response = requests.post(self.url,json={"state":state,"discriminator":discriminator,"auth":self.auth_token})
        if response.status_code == 200 and response.text == "Success":
            return True
        else:
            return response.text
        
    def _is_enabled(self):
        res = os.getenv("LIGHT_CONTROLLER_ENABLED")
        if res == "YES":
            return True
        else:
            return False
    
    def get_time(self):
        # Define the timezone for Phoenix, Arizona
        phoenix_tz = pytz.timezone('America/Phoenix')
        
        # Get the current time in Phoenix, Arizona
        current_time = datetime.now(phoenix_tz)
        
        # Check if it's between the hours of 8am and 10pm
        if current_time.hour >= 8 and current_time.hour < 22:
            return True
        else:
            print(current_time.hour)
            return False
        
    def turn_on(self):
        #This will be called when someone unlocks the door.
        if self.get_time() and self._is_enabled():
            return self._send_command("on","both")
        
        
    def turn_off(self):
        if self._is_enabled():
        #This might not be called, but it's here
            return self._send_command("off","both")


if __name__ == "__main__":
    import time
    test = LightControllerHook()
    print(test.turn_on())
    time.sleep(3)
    print(test.turn_off())
    time.sleep(3)
    print(test.turn_on())