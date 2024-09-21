from flask import Flask, render_template, request, jsonify, redirect, send_file
import json
import time
import threading
from datetime import datetime, timedelta
import os

from door_controller import DoorController
from version_control import VersionControl
from auth_manager import AuthManager
auth_manager = AuthManager()

print("attempting to connect to network")
print(auth_manager.attemptWifi())

from tunnel_manager import Tunnel

tunnel = Tunnel()
tunnel.installAndRunDocker(tunnel.download())

def tunnel_status_manager():
    print("The tunnel status manager is starting.")
    while True:
        if not tunnel.docker_container_status():
            print("The tunnel does not exist! Attempting to create a new one...")
            while not tunnel.docker_container_status():
                print("Attempting to create a new tunnel...")

                if not tunnel.installAndRunDocker():
                    print("Error: Could not create a new tunnel.")

                time.sleep(5)
        print("Tunnel exists. Will check again in 60 seconds.")
        time.sleep(60)

threading.Thread(target=tunnel_status_manager).start()

from log import LogHandler

from registrar_server import RegistrarClient

app = Flask(__name__)

verification_rate_limit_per_second = 1
last_verification_time = 0

version_control = VersionControl()
log_handler = LogHandler()
registrar = RegistrarClient()

last_verification_times = {}  # Dictionary to track last verification time per IP

# Store active time requests in memory
active_times = []

def start_registrar():
    log_handler.log_message("Registrar server started")
    log_handler.log_message("Device IP: " + registrar.get_ip())
    log_handler.log_message("Device Serial: " + registrar.get_serial_number())
    while True:
        print("Task: Pushing IP to registrar server")
        print(registrar.push_to_registrar())
        time.sleep(3600)
    
def check_wifi_status():
    while True:
        if not auth_manager.check_wifi_connection():
            print("Error: No WiFi connection")
            log_handler.log("Error: No WiFi connection")
            version_control.restartDevice()
        time.sleep(60)

wifi_thread = threading.Thread(target=check_wifi_status)
wifi_thread.start()

registrar_thread = threading.Thread(target=start_registrar)
registrar_thread.start()

def runSetupServer():
    os.system("python -m setup.main")

if not auth_manager.setup_complete_status():
    registrar.push_to_startup_registrar()
    runSetupServer()
    print("File exited")

else:
    door_controller = DoorController(False) # False to make it calibrate out loud (then the user knows it's online)

    def door_controller_main_loop():
        while True:
            door_controller.main_loop_single_runnable()
            time.sleep(1)

    threading.Thread(target=door_controller_main_loop).start()

    #Ensure SSL is valid
    auth_counter = 0
    while not auth_manager.verify_ssl_keys():
        auth_counter += 1
        if auth_counter > 3:
            print("Error: Too many errors.")
            log_handler.log("CRTICAL: Too many errors when verifying SSL keys. Exiting.")
            exit(1)

    print("SSL keys verified (main).")

    def unlockDoor():
        door_controller.unlock()
        return

    def lockDoor():
        door_controller.lock()
        return

    @app.route('/')
    def main_checker():
        """Checks for times and renders the appropriate page."""
        removeOverdueTimes()

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
        if auth_manager.get_wifi_failed_usernames():
            if not check_password():
                return redirect('/unlocking_door_page')
            return redirect('/unlocking_door_page?wifi_warning=' + auth_manager.get_wifi_failed_usernames()[0])
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

        data = request.json

        if data['redirect'] == "ignore":
            t = threading.Thread(target=unlockDoor)
            t.start()
            return json.dumps({'status': 'success'})
        return json.dumps({'status': 'success'})

    # Password protected function for checking passwords in cookies
    def check_password():
        """Helper function to check password from cookies."""
        cookie_password = request.cookies.get('doorlock-passcode')
        return auth_manager.password_exists(cookie_password)

    @app.route('/setTime', methods=['POST'])
    def set_time():
        """Sets a privacy or quiet time."""
        global active_times
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

    def removeOverdueTimes():
        """Removes any overdue time requests."""
        global active_times
        now = datetime.now()
        for time_entry in active_times:
            end_time_str = time_entry['endTime']
            end_time = datetime.strptime(end_time_str, '%I:%M %p')
            end_time = now.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)
            if now > end_time:
                active_times.remove(time_entry)

    @app.route('/getCurrentTimes', methods=['GET'])
    def get_current_times():
        """Returns all active time requests."""
        if not check_password():
            return jsonify({'status': 'fail', 'message': 'Invalid password'}), 403

        removeOverdueTimes()

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

    @app.route('/support')
    def support():
        """Renders the support page."""
        if not check_password():
            return redirect('/password?redirect=support')
        return render_template('support.html')

    @app.route('/serial', methods=['GET', 'POST'])
    def serial():
        """Returns the serial number of the device."""
        if not check_password():
            return jsonify({'status': 'fail', 'message': 'Invalid password'}), 403
        return jsonify({'serialNumber': registrar.get_serial_number()})

    @app.route('/change-password')
    def change_password():
        """Renders the change password page."""
        if not check_password():
            return redirect('/password?redirect=change-password')
        return render_template('change-password.html')

    @app.route('/changepassword', methods=['POST'])
    def change_password_action():
        """Changes the password for the user. This is a POST request."""
        # Passwords are sent in plaintext, because we use HTTPS so it's encrypted

        if not check_password():
            return jsonify({'status': 'fail', 'message': 'Invalid password'}), 403

        try:
            data = request.json

            old_password = data.get('old_password')
            new_password = data.get('new_password')
            pin = data.get('pin')

            current_password = auth_manager.currentPassword(pin)
            if current_password is None:
                return jsonify({'status': 'fail', 'message': 'Invalid PIN'}), 403

            if old_password == current_password:
                auth_manager.changePassword(pin, new_password)
                return jsonify({'status': 'success'})
            
            return jsonify({'status': 'fail', 'message': 'Incorrect old password'}), 403
        except Exception as e:
            return jsonify({'status': 'fail', 'message': str(e)}), 500
        
    # @app.route('/c')
    # def send_certificate():
    #     """Send the certificate file to the user so they can trust it."""
    #     return send_file(auth_manager.cert_as_binary(), as_attachment=True, download_name='cert.pem')

    if __name__ == '__main__':
        #app.run(host='0.0.0.0', port=5000)
        #app.run(ssl_context=('/home/pi/Desktop/webserver/ssl_keys/cert.pem', '/home/pi/Desktop/webserver/ssl_keys/key.pem'), host='0.0.0.0', port=5000)
        app.run(port=5000)