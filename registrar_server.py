import os
import requests
from dotenv import load_dotenv
from colorama import Fore
import secrets
import string

load_dotenv()

def randomAlphaNumericString(stringLength=8):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(secrets.choice(lettersAndDigits) for i in range(stringLength))

class RegistrarClient:
    def __init__(self):
        load_dotenv()
        self.secret = os.getenv('DEVICE_SECRET')  # Never share this! It is used to authenticate the device with the registrar server
        self.default_registrar = 'https://registrar.philipehrbright.com'
        self.startup_url = 'https://registrar.philipehrbright.com/startup/'  # The PHP endpoint
        if self.secret is None:
            print(Fore.RED + "Error: DEVICE_SECRET not found in .env file.")
            self.secret = randomAlphaNumericString(16)
            print(Fore.YELLOW + "Generated random secret: " + self.secret + ". Adding it to the .env file.")
            with open('.env', 'a') as f:
                f.write('\nDEVICE_SECRET=' + self.secret + '\n')

    def create_registrar_list(self):
        '''
        Creates the registrar file if it does not already exist and adds the default registrar to the file
        '''
        if os.path.exists('registrar_list.txt'):
            print(Fore.GREEN + "Registrar list exists.")
            return None

        print(Fore.YELLOW + "Registrar list does not exist. Creating default registrar list.")
        with open('registrar_list.txt', 'w+') as f:
            f.write(self.default_registrar)
        return 'File created'

    def get_active_registrar(self):
        '''
        Returns the first registrar server that is reachable.
        '''
        try:
            with open('registrar_list.txt', 'r') as f:
                for line in f:
                    registrar = line.strip()
                    if registrar == '' or not self.check_registrar_security(registrar):
                        print(Fore.YELLOW + "Warning! Skipping registrar (unsecure): " + registrar)
                        continue

                    registrar_request_status = requests.get(registrar + '/status')
                    if registrar_request_status.status_code == 200 and registrar_request_status.text == 'OK':
                        return registrar
            return None
        except Exception as e:
            return "Error:" + str(e)

    def get_ip(self):
        '''
        Returns the IP of the device
        '''
        res = os.popen('ip addr show | grep "inet " | grep -v 127.0.0.1 | cut -d " " -f 6 | cut -d "/" -f 1').read().strip()
        return res.split('\n')[0]

    def get_serial_number(self):
        '''
        Returns the serial number of the device
        '''
        s = os.popen('cat /proc/cpuinfo | grep Serial | cut -d " " -f 2').read().strip()
        while s[0] == '0':
            s = s[1:]
        return s

    def check_registrar_security(self, registrar: str):
        '''
        Checks if the registrar server is secure by checking if the URL starts with 'https'
        '''
        return registrar[:5] == 'https'

    def push_to_registrar(self):
        ip = self.get_ip()
        serial = self.get_serial_number()
        registrar = self.get_active_registrar()

        registrar_error_counter = 0
        while registrar is None or "Error" in registrar:
            if self.create_registrar_list() is not None:
                print(Fore.RED + "Uh oh! No registrar list found, unable to push IP")
                print(Fore.RED + "Attempting to create a default registrar list")
            elif registrar is None:
                print(Fore.RED + "No active registrar found. This means we checked all the registrars in the list and none of them are reachable.")
                print(Fore.RED + "Please check with the system administrator to make sure the registrar server is up and running.")
            else:
                print(Fore.RED + "Error: " + registrar)

            registrar_error_counter += 1

            # Refresh the registrar list
            registrar = self.get_active_registrar()

            if registrar_error_counter > 3:
                print(Fore.RED + "Error: Too many errors.")
                return "Error: Too many errors."

        print(Fore.BLUE + "Pushing IP to registrar server: " + str(registrar))
        if not self.check_registrar_security(registrar):
            print(Fore.RED + "Error: Registrar server is not secure.")
            return "Error: Registrar server is not secure!"

        try:
            # Push IP to registrar
            registrar_post = requests.post(registrar, data={'ip': ip, 'serial': serial, 'secret': self.secret})
            if registrar_post.status_code == 200:
                print(Fore.GREEN + "IP successfully pushed to registrar")
                print(Fore.GREEN + "Registrar Response: " + registrar_post.text)
                return "IP successfully pushed to registrar"
            else:
                print(Fore.RED + "Error: Unable to push IP to registrar")
                print(Fore.YELLOW + "Registrar Response: " + registrar_post.text)
                print(Fore.YELLOW + "Registrar Status Code: " + str(registrar_post.status_code))
                return "Error: Unable to push IP to registrar"
        except Exception as e:
            print(Fore.RED + "Error: Unable to push IP to registrar")
            return f"Error: Unable to push IP to registrar ({str(e)})"

    def send_to_php(self, ip, serial, secret):
        '''
        Sends IP, Serial, and Secret to PHP endpoint
        '''
        try:
            response = requests.post(self.startup_url, data={'IP': ip, 'Serial': serial, 'Secret': secret})
            if response.status_code == 200:
                print(Fore.GREEN + "Information successfully sent to PHP endpoint")
            else:
                print(Fore.RED + "Failed to send information to PHP endpoint")
                print(Fore.YELLOW + "PHP Response: " + response.text)
        except Exception as e:
            print(Fore.RED + f"Error: Unable to send information to PHP endpoint ({str(e)})")

    def push_to_startup_registrar(self):
        ip = self.get_ip()
        serial = self.get_serial_number()
        secret = self.get_secret()
        self.send_to_php(ip, serial, secret)
        print(Fore.GREEN + "IP, Serial, and Secret sent to PHP endpoint")
        return True

    def get_secret(self):
        return self.secret

    def main(self):
        print(Fore.WHITE + "Serial Number: " + self.get_serial_number())
        print(Fore.WHITE + "Device Secret: " + str(self.secret))
        print(Fore.WHITE + "IP: " + self.get_ip())
        #print(Fore.WHITE + "Registrar Output: " + self.push_to_registrar())

    def push_tunnel(self, tunnel_ip):
        ip = self.get_ip()
        serial = self.get_serial_number()
        registrar = self.get_active_registrar()

        registrar_error_counter = 0
        while registrar is None or "Error" in registrar:
            if self.create_registrar_list() is not None:
                print(Fore.RED + "Uh oh! No registrar list found, unable to push IP")
                print(Fore.RED + "Attempting to create a default registrar list")
            elif registrar is None:
                print(Fore.RED + "No active registrar found. This means we checked all the registrars in the list and none of them are reachable.")
                print(Fore.RED + "Please check with the system administrator to make sure the registrar server is up and running.")
            else:
                print(Fore.RED + "Error: " + registrar)

            registrar_error_counter += 1

            # Refresh the registrar list
            registrar = self.get_active_registrar()

            if registrar_error_counter > 3:
                print(Fore.RED + "Error: Too many errors.")
                return "Error: Too many errors."

        print(Fore.BLUE + "Pushing IP to registrar server: " + str(registrar))
        if not self.check_registrar_security(registrar):
            print(Fore.RED + "Error: Registrar server is not secure.")
            return "Error: Registrar server is not secure!"

        try:
            # Push IP to registrar
            registrar_post = requests.post(registrar, data={'ip': ip, 'serial': serial, 'secret': self.secret, 'tunnel_ip': tunnel_ip})
            if registrar_post.status_code == 200:
                print(Fore.GREEN + "IP successfully pushed to registrar")
                print(Fore.GREEN + "Registrar Response: " + registrar_post.text)
                return "IP successfully pushed to registrar"
            else:
                print(Fore.RED + "Error: Unable to push IP to registrar")
                print(Fore.YELLOW + "Registrar Response: " + registrar_post.text)
                print(Fore.YELLOW + "Registrar Status Code: " + str(registrar_post.status_code))
                return "Error: Unable to push IP to registrar"
        except Exception as e:
            print(Fore.RED + "Error: Unable to push IP to registrar")
            return f"Error: Unable to push IP to registrar ({str(e)})"


if __name__ == '__main__':
    client = RegistrarClient()
    client.main()
    run_test = input("Run test? (y/n): ")
    if run_test == "y":
        client.push_to_registrar()
        # Call the `send_to_php` method if you need to test sending to the PHP endpoint separately
        ip = client.get_ip()
        serial = client.get_serial_number()
        secret = client.get_secret()
        client.send_to_php(ip, serial, secret)
    else:
        print(Fore.YELLOW + "Test skipped.")
