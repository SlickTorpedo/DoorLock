from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

def decrypt(encrypted_data, key_base64, iv_base64):
    """Decrypt the data using AES with the provided key and IV."""
    print("Decrypting data...")

    # Decode key and IV from Base64
    key = base64.b64decode(key_base64)
    iv = base64.b64decode(iv_base64)
    encrypted_data = base64.b64decode(encrypted_data)

    # Print lengths for debugging
    print(f"Key length: {len(key)}")
    print(f"IV length: {len(iv)}")

    # Check key length
    if len(key) not in (16, 24, 32):
        raise ValueError("Incorrect AES key length")

    # Create cipher object
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # Decrypt and unpad data
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    
    print(f"Decrypted data: {decrypted_data.decode('utf-8')}")  # Decode bytes to string
    return decrypted_data.decode('utf-8')

# Example usage
encrypted_data = "QWAd0V2K5cm5EIzK795QKtsH2IGbFVjkq22PJI+OqEI="  # base64 encoded encrypted data from JavaScript
key_base64 = "MTIzNDAwMDAwMDAwMDAwMA=="       # base64 encoded key from JavaScript
iv_base64 = "F5G1rs5/TejhovBwD/UmQA=="        # base64 encoded IV from JavaScript

decrypted_message = decrypt(encrypted_data, key_base64, iv_base64)