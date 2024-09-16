import os
import json
import dotenv

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

        print("Room number: " + self.room_number)
        print("Users: " + str(self.users))
        # The number is the PIN while the string is the password

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

        # Print lengths for debugging

        # Create cipher object
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt and unpad data
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        
        #print(f"Decrypted data: {decrypted_data.decode('utf-8')}")  # Decode bytes to string
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
