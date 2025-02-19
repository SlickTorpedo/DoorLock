import requests

#This file is dedicated to the saftey measures that prevent the device from locking you out of your room.
class Lockout:
    def __init__(self, device_url):
        self.device_url = device_url #This is the URL, for example "https://doorlock-1.philipehrbright.tech" or whatever
    
    def check_lockout(self):
        '''
        Checks if the device is locked out
        '''
        try:
            response = requests.get(self.device_url + '/lockoutping')
            if response.status_code == 200:
                return True
            else:
                try:
                    print("[LOCKOUT] Self Ping Response: " + str(response.text))
                    print("[LOCKOUT] Self Ping Status Code: " + str(response.status_code))
                except:
                    print("[LOCKOUT] Self Ping Response: Unable to display")
                    print("[LOCKOUT] Self Ping Status Code: Unable to display")
                return False
        except Exception as e:
            print("[LOCKOUT] Error:" + str(e))
            return False