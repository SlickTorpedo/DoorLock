from flask import Flask, render_template, request, jsonify, redirect
import json
import time
import os
from dotenv import load_dotenv
import threading
from datetime import datetime, timedelta

from door_controller import DoorController
from version_control import VersionControl
from log import LogHandler

load_dotenv()
master_password = os.getenv('MASTER_PASSWORD')

app = Flask(__name__)

verification_rate_limit_per_second = 1
last_verification_time = 0

door_controller = DoorController()
version_control = VersionControl()
log_handler = LogHandler()

last_verification_times = {}  # Dictionary to track last verification time per IP

# Store active time requests in memory
active_times = []

def unlockDoor():
    door_controller.unlock()
    return

def lockDoor():
    door_controller.lock()
    return

@app.route('/')
def main_checker():
    """Checks for times and renders the appropriate page."""
    now = datetime.now()
    
    # Example: [{'id': 1, 'type': 'privacy', 'endTime': '05:07 PM'}]
    for time_entry in active_times:
        end_time_str = time_entry['endTime']
        # Assuming end_time is today initially
        end_time = datetime.strptime(end_time_str, '%I:%M %p')
        
        # Set the end_time to today's date
        end_time = now.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)
        
        # If end_time is before now, assume it’s for the next day
        if end_time < now:
            end_time += timedelta(days=1)

        if now < end_time:
            if time_entry['type'] == 'privacy':
                return render_template('requesting_privacy.html')
            elif time_entry['type'] == 'quiet':
                return render_template('requesting_quiet.html')
    
    # Redirect to the unlocking door page if no active times
    return redirect('/unlocking_door_page')

@app.route('/unlocking_door_page')
def unlocking_door_page():
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
    lockDoor()
    return render_template('locked.html')

@app.route('/software_update')
def software_update():
    """Renders the software update page."""
    return render_template('software_update.html')

@app.route('/update_check', methods=['POST'])
def update_check():
    """Checks for updates."""
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

    # Check password from cookies
    if not check_password():
        return json.dumps({'status': 'fail'}), 403

    last_verification_times[ip_address] = current_time
    log_handler.log_message("Software update initiated")
    if version_control.update():
        return json.dumps({'status': 'success'})
    log_handler.log_message("Software update failed")
    return json.dumps({'status': 'fail'}), 400

@app.route('/door_unlocked_static')
def door_unlocked_static():
    """Renders the door unlocked static page."""
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

    # Check password from cookies
    if not check_password():
        return json.dumps({'status': 'fail'}), 403

    last_verification_times[ip_address] = current_time
    t = threading.Thread(target=unlockDoor)
    t.start()
    return json.dumps({'status': 'success'})

# Password protected function for checking passwords in cookies
def check_password():
    """Helper function to check password from cookies."""
    cookie_password = request.cookies.get('doorlock-passcode')
    return cookie_password == master_password

@app.route('/setTime', methods=['POST'])
def set_time():
    """Sets a privacy or quiet time."""
    if not check_password():
        return jsonify({'status': 'fail', 'message': 'Invalid password'}), 403

    data = request.json
    time_type = data['type']
    end_time = data['endTime']
    end_time_dt = datetime.strptime(end_time, '%I:%M %p')
    
    # Adjust for today or tomorrow
    now = datetime.now()
    if end_time_dt < now:
        end_time_dt += timedelta(days=1)
    
    active_times.append({
        'id': len(active_times) + 1,  # Simple ID generation
        'type': time_type,
        'endTime': end_time_dt.strftime('%I:%M %p')
    })
    
    return jsonify({'status': 'success'})

@app.route('/getCurrentTimes', methods=['GET'])
def get_current_times():
    """Returns all active time requests."""
    if not check_password():
        return jsonify({'status': 'fail', 'message': 'Invalid password'}), 403

    return jsonify({'activeTimes': active_times})

@app.route('/extendTime', methods=['POST'])
def extend_time():
    """Extends the end time of an active time request."""
    if not check_password():
        return jsonify({'status': 'fail', 'message': 'Invalid password'}), 403

    data = request.json
    id = data['id']
    extension = data['extension']
    
    for time_entry in active_times:
        if time_entry['id'] == id:
            end_time_dt = datetime.strptime(time_entry['endTime'], '%I:%M %p')
            end_time_dt += timedelta(minutes=extension)
            time_entry['endTime'] = end_time_dt.strftime('%I:%M %p')
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'fail'}), 404

@app.route('/cancelTime', methods=['POST'])
def cancel_time():
    """Cancels an active time request."""
    if not check_password():
        return jsonify({'status': 'fail', 'message': 'Invalid password'}), 403

    data = request.json
    id = data['id']
    
    global active_times
    active_times = [time_entry for time_entry in active_times if time_entry['id'] != id]
    
    return jsonify({'status': 'success'})

@app.route('/request_time')
def request_time():
    """Renders the request time page."""
    if not check_password():
        return redirect('/password?redirect=request_time')

    return render_template('request_action.html')

# Start the registrar server 
from registrar_server import RegistrarClient
registrar = RegistrarClient()

def start_registrar():
    log_handler.log_message("Registrar server started")
    log_handler.log_message("Device IP: " + registrar.get_ip())
    log_handler.log_message("Device Serial: " + registrar.get_serial_number())
    while True:
        print("Task: Pushing IP to registrar server")
        print(registrar.push_to_registrar())
        time.sleep(3600)

registrar_thread = threading.Thread(target=start_registrar)
registrar_thread.start()

main_loop_door_controller = threading.Thread(target=door_controller.main_loop)
main_loop_door_controller.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
