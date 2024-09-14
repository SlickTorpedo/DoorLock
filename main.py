from flask import Flask, render_template, request
import json
import time
import os
from dotenv import load_dotenv
import threading

from pin_handler import PinHandler
from version_control import VersionControl

load_dotenv()
master_password = os.getenv('MASTER_PASSWORD')

app = Flask(__name__)

verification_rate_limit_per_second = 1
last_verification_time = 0

door_pin_handler = PinHandler()
version_control = VersionControl()

last_verification_times = {}  # Dictionary to track last verification time per IP

def unlockDoor():
    door_pin_handler.unlock_door()
    return

@app.route('/')
def unlocking_door():
    """Renders the unlocking door page."""
    return render_template('unlocking_door.html')

@app.route('/password')
def password():
    """Renders the password page."""
    return render_template('password.html')

@app.route('/rate_limit')
def rate_limit():
    """Renders the rate limit page."""
    return render_template('rate_limit.html')

@app.route('/error')
def error():
    """Renders the error page."""
    return render_template('error.html')

@app.route('/lock')
def lock():
    """Locks the door."""
    door_pin_handler.lock_door()
    return render_template('locked.html')

@app.route('/software_update')
def software_update():
    """Renders the software update page."""
    return render_template('software_update.html')

@app.route('/update_check')
def update_check():
    """Checks for updates."""
    #return json.dumps({'update_pending': False})
    if version_control.check_for_updates():
        return json.dumps({'update_pending': True})
    return json.dumps({'update_pending': False})

@app.route('/update', methods=['POST'])
def update():
    """Updates the software."""
    
    ip_address = request.remote_addr
    current_time = time.time()

    # Set the default last verification time if IP is new
    if ip_address not in last_verification_times:
        last_verification_times[ip_address] = 0

    if current_time - last_verification_times[ip_address] < verification_rate_limit_per_second:
        return json.dumps({'status': 'rate_limit_exceeded'})

    password = request.json['password']

    if password == master_password:
        last_verification_times[ip_address] = current_time
        if version_control.update():
            return json.dumps({'status': 'success'})
        return json.dumps({'status': 'fail'}), 400
    else:
        last_verification_times[ip_address] = current_time
        return json.dumps({'status': 'fail'})

@app.route('/door_unlocked_static')
def door_unlocked_static():
    """Renders the door unlocked static page."""
    #This is here because safari will reload the page again when you view all your tabs, and this causes the door to unlock in the background.
    return render_template('door_unlocked_static.html')

@app.route('/software_update_recommended')
def software_update_recommended():
    """Renders the software update recommended page."""
    return render_template('software_update_recommended.html')

@app.route('/verify', methods=['POST'])
def verify():
    """Backend system for verifying the password."""
    ip_address = request.remote_addr
    current_time = time.time()

    # Set the default last verification time if IP is new
    if ip_address not in last_verification_times:
        last_verification_times[ip_address] = 0

    if current_time - last_verification_times[ip_address] < verification_rate_limit_per_second:
        return json.dumps({'status': 'rate_limit_exceeded'})

    password = request.json['password']

    if password == master_password:
        last_verification_times[ip_address] = current_time
        t = threading.Thread(target=unlockDoor)
        t.start()
        return json.dumps({'status': 'success'})
    else:
        last_verification_times[ip_address] = current_time
        return json.dumps({'status': 'fail'})

#Start the registrar server 
from registrar_server import RegistrarClient
registrar = RegistrarClient()

def start_registrar():
    while True:
        print("Task: Pushing IP to registrar server")
        print(registrar.push_to_registrar())
        time.sleep(3600)

registrar_thread = threading.Thread(target=start_registrar)
registrar_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
