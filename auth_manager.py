import os
import json
import dotenv
import subprocess
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

class AuthManager:
    def __init__(self):
        # Parse the environment variable as a JSON string and then load it as a Python object
        passwords_json = os.getenv('PASSWORDS')
        if passwords_json:
            # Convert the JSON string into a Python list
            passwords_list = json.loads(passwords_json)
            if passwords_list and isinstance(passwords_list, list):
                # Assume the list contains one dictionary
                self.passwords = passwords_list[0] if isinstance(passwords_list[0], dict) else {}
            else:
                self.passwords = {}
        else:
            self.passwords = {}
        
        self.room_number = os.getenv('ROOM_NUMBER')
        self.users = os.getenv('USERS').split(',') if os.getenv('USERS') else []

        # Define paths for SSL/TLS keys and timestamp file
        self.key_path = '/home/pi/Desktop/webserver/ssl_keys/key.pem'
        self.csr_path = '/home/pi/Desktop/webserver/ssl_keys/csr.pem'
        self.cert_path = '/home/pi/Desktop/webserver/ssl_keys/cert.pem'
        self.timestamp_path = '/home/pi/Desktop/webserver/ssl_keys/timestamp.txt'

        try:
            print("Room number: " + self.room_number)
            print("Users: " + str(self.users))
        except:
            print("Error loading room number and users. The ENV file may be missing or not setup yet!")

    def is_valid_password(self, pin, password):
        """Checks if the provided password is correct."""
        if pin in self.passwords:
            return self.passwords[pin] == password
        return False
    
    def password_exists(self, password):
        return password in self.passwords.values()
    
    def decrypt(self, encrypted_data, pin, iv_base64):
        """Decrypt the data using AES with the provided key and IV."""
        # Decode key and IV from Base64
        key = str(pin).encode('utf-8')  # Convert string to bytes
        iv = base64.b64decode(iv_base64)
        encrypted_data = base64.b64decode(encrypted_data)

        # Create cipher object
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt and unpad data
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        
        return decrypted_data.decode('utf-8')

    def currentPassword(self, pin):
        return self.passwords.get(pin, None)
    
    def listPins(self):
        return self.passwords.keys()
    
    def listPasswords(self):
        return self.passwords.values()
    
    def changePassword(self, pin, newPassword):
        self.passwords[pin] = newPassword
        print("Password changed for pin " + pin + " to " + newPassword)
        dotenv.set_key(dotenv_file, 'PASSWORDS', json.dumps([self.passwords]))
        return self.passwords

    def generate_ssl_keys(self):
        """Generate SSL/TLS keys and certificate."""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.key_path), exist_ok=True)

        # Generate the private key
        subprocess.run(['openssl', 'genrsa', '-out', self.key_path, '2048'], check=True)
        print("Private key generated.")

        # Generate the CSR
        subj = "/C=US/ST=Arizona/L=Tucson/O=Not applicable/CN=localhost"
        subprocess.run(['openssl', 'req', '-new', '-key', self.key_path, '-out', self.csr_path, '-subj', subj], check=True)
        print("CSR generated.")

        # Generate the self-signed certificate
        subprocess.run(['openssl', 'x509', '-req', '-days', '365', '-in', self.csr_path, '-signkey', self.key_path, '-out', self.cert_path], check=True)
        print("Self-signed certificate generated.")

        # Update timestamp
        with open(self.timestamp_path, 'w') as f:
            f.write(datetime.now().isoformat())
        print("Timestamp updated.")

    def cert_as_binary(self):
        #Return the cert as a binary file-like objects
        return open(self.cert_path, 'rb')

    def verify_ssl_keys(self):
        """Verify if SSL/TLS keys and certificate exist and are valid."""
        # Check if key, CSR, and certificate files exist
        if (os.path.isfile(self.key_path) and 
            os.path.isfile(self.csr_path) and 
            os.path.isfile(self.cert_path)):

            # Check the timestamp file
            if os.path.isfile(self.timestamp_path):
                with open(self.timestamp_path, 'r') as f:
                    timestamp = f.read().strip()
                last_generated = datetime.fromisoformat(timestamp)
                current_time = datetime.now()
                # Check if certificate is older than 365 days
                if current_time - last_generated > timedelta(days=365):
                    print("Certificate expired. Generating new SSL/TLS keys and certificate...")
                    self.generate_ssl_keys()
                    return False
                else:
                    print("SSL/TLS keys and certificate are up to date.")
                    return True
            else:
                print("Timestamp file missing. Generating new SSL/TLS keys and certificate...")
                self.generate_ssl_keys()
                return False
        else:
            print("SSL/TLS keys or certificate are missing. Generating now...")
            self.generate_ssl_keys()
            return False
    

    def attemptWifi(self):
        # Check if the file exists
        if os.path.exists('/etc/NetworkManager/system-connections/UAWiFi.nmconnection'):
            print("UA-WiFi exists. Attempting to ping google.com...")
            # Try and ping google.com
            try:
                subprocess.run(['ping', '-c', '1', 'google.com'], check=True)
                print("Ping successful.")
                return True
            except subprocess.CalledProcessError:
                print("Ping failed. Attempting to connect to network manually...")

        # Construct the configuration string
        for username, password in zip(os.getenv('UA_USERNAME'), os.getenv('UA_PASSWORD')):
            config = f"""[connection]
id=UAWiFi
uuid=0fee18d8-f12d-4224-a53c-66f7b94de057
type=wifi
interface-name=wlan0

[wifi]
mode=infrastructure
ssid=UAWiFi

[wifi-security]
auth-alg=open
key-mgmt=wpa-eap

[802-1x]
eap=ttls;
identity={username}
password={password}
phase2-auth=mschapv2

[ipv4]
method=auto

[ipv6]
addr-gen-mode=default
method=auto

[proxy]
    """

            # Use echo and sudo to write to the file
            try:
                subprocess.run(['sudo', 'bash', '-c', f'echo "{config}" > /etc/NetworkManager/system-connections/UAWiFi.nmconnection'], check=True)
                print("Configuration written to /etc/NetworkManager/system-connections/UA-WiFi.")

                # Restart the network manager
                subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager.service'], check=True)
                print("Network manager restarted.")

                # Attempt to ping google.com again
                try:
                    subprocess.run(['ping', '-c', '1', 'google.com'], check=True)
                    print("Ping successful.")
                    return True
                except subprocess.CalledProcessError:
                    print("Ping failed.")
            except subprocess.CalledProcessError:
                print("Failed to write configuration or restart network manager.")
        
        return False

                


    def set_submit_setup_data(self, data):
    # Directly work with data as it's already a dictionary
        room_number = data['roomNumber'].strip()
        self.room_number = room_number
        self.users = [data['roommate_1']['name'], data['roommate_2']['name']]

        # Extract the other information
        roommate_1 = data['roommate_1']
        roommate_2 = data['roommate_2']

        roomate_1_pin = roommate_1['pin']
        roomate_1_password = roommate_1['password']
        roomate_1_ua_username = roommate_1['uaLogin']['username']
        roomate_1_ua_password = roommate_1['uaLogin']['password']


        roomate_2_pin = roommate_2['pin']
        roomate_2_password = roommate_2['password']
        roomate_2_ua_username = roommate_2['uaLogin']['username']
        roomate_2_ua_password = roommate_2['uaLogin']['password']

        # Update the .env file
        current_env = {}
        current_env['DEVICE_SECRET'] = os.getenv('DEVICE_SECRET')
        current_env['ROOM_NUMBER'] = room_number
        current_env['USERS'] = ','.join(self.users)
        current_env['PASSWORDS'] = json.dumps([{roomate_1_pin: roomate_1_password, roomate_2_pin: roomate_2_password}])
        current_env['UA_USERNAME'] = json.dumps([roomate_1_ua_username, roomate_2_ua_username])
        current_env['UA_PASSWORD'] = json.dumps([roomate_1_ua_password, roomate_2_ua_password])

        # Update the .env file
        with open(dotenv_file, 'w') as f:
            for key, value in current_env.items():
                f.write(f"{key}={value}\n")

        #Append complete setup to the .env file
        with open(dotenv_file, 'a') as f:
            f.write("SETUP_STATUS=complete\n")

        print("Data written to .env file.")

        return True
    
    def setup_complete_status(self):
        return os.getenv('SETUP_STATUS') == 'complete'



if __name__ == '__main__':
    auth_manager = AuthManager()
    print(auth_manager.room_number)
    print("Attempting to connect to UA-WiFi...")
    print(auth_manager.attemptWifi())
    print("Setup complete status: " + str(auth_manager.setup_complete_status()))
    print("Users: " + str(auth_manager.users))
    print("Passwords: " + str(auth_manager.passwords))
    print("Room number: " + str(auth_manager.room_number))
    print("SSL keys verified: " + str(auth_manager.verify_ssl_keys()))