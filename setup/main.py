#This server is used when setting up the device, calibrating it, and testing it.

#It is intended to be used by the system administrator, and is not intended to be used by the end user.

from flask import Flask, render_template, request

from ..registrar_server import RegistrarClient
from ..auth_manager import AuthManager
from ..log import LogHandler

registrar_client = RegistrarClient()
auth_manager = AuthManager()
log_handler = LogHandler()

#Ensure SSL is valid
auth_counter = 0
while not auth_manager.verify_ssl_keys():
    auth_counter += 1
    if auth_counter > 3:
        print("Error: Too many errors.")
        log_handler.log("CRTICAL: Too many errors when verifying SSL keys. Exiting.")
        exit(1)

app = Flask(__name__)

def check_password():
    """Helper function to check password from cookies."""
    cookie_password = request.cookies.get('doorlock-passcode')
    return registrar_client.get_secret() == cookie_password

@app.route('/')
def setup_main():
    """Checks for times and renders the appropriate page."""
    return render_template('locked.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
