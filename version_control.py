import requests
import os

class VersionControl:
    def __init__(self):
        self.repo_url = "https://github.com/SlickTorpedo/DoorLock"
        self.version_url = "https://raw.githubusercontent.com/SlickTorpedo/DoorLock/main/version.txt"
    
    def check_for_updates(self):
        '''
        Checks the repo for updates
        '''
        try:
            current_version = self.get_current_version()
            latest_version = self.get_latest_version()
            if current_version != latest_version:
                return True
            return False
        except:
            return False
        
    def get_current_version(self):
        '''
        Returns the current version of the software
        '''
        try:
            with open('version.txt', 'r') as f:
                return f.read().strip()
        except:
            with open('version.txt', 'w+') as f:
                f.write('0.0.0')
            
    def get_latest_version(self):
        '''
        Returns the latest version of the software
        '''
        return requests.get(self.version_url).text.strip()
    
    def update(self):
        '''
        Updates the software
        '''
        try:
            os.system(f'git clone {self.repo_url} updated_software')
            os.system('cp -r updated_software/* .')
            os.system('rm -rf updated_software')
            os.system('pip install -r requirements.txt --break-system-packages')
            print("Ending the program so the changes can take effect. Goodbye!")
            exit()
            return True
        except:
            return False