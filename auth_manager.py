import os
import json
from dotenv import load_dotenv

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64

load_dotenv()

class AuthManager:
    def __init__(self):
        self.passwords = json.loads(os.getenv('PASSWORDS'))
        #Example: [ { "1234": "admin", "0001": "helloworld" } ]
        #The number is the PIN while the string is the password

    def is_valid_password(self, pin, password):
        """Checks if the provided password is correct."""
        if pin in self.passwords:
            return self.passwords[pin] == password
        return False
    
    def decrypt(self, encrypted_data, key, iv_base64):
        """Decrypt the data using AES with the provided key and IV."""
        iv = base64.b64decode(iv_base64)
        encrypted_data = base64.b64decode(encrypted_data)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()
        return decrypted_data.decode()

    def currentPassword(self, pin):
        return self.passwords[pin]
    
    def listPins(self):
        return self.passwords.keys()
    
    def listPasswords(self):
        return self.passwords.values()
    
    def changePassword(self, pin, newPassword):
        self.passwords[pin] = newPassword
        return self.passwords
