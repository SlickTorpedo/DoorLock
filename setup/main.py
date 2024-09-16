#This server is used when setting up the device, calibrating it, and testing it.

#It is intended to be used by the system administrator, and is not intended to be used by the end user.

#Important! You cannot run this file normally, you will get an import error. You must run it from the root directory using "python -m setup.main".

from flask import Flask, render_template, request, send_file, redirect

from colorama import Fore

from registrar_server import RegistrarClient
from auth_manager import AuthManager
from log import LogHandler

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

print(Fore.GREEN + "SSL keys verified.")
app = Flask(__name__)

def check_password():
    """Helper function to check password from cookies."""
    cookie_password = request.cookies.get('debug-secret')
    return registrar_client.get_secret() == cookie_password

@app.route('/c')
def send_certificate():
    """Send the certificate file to the user so they can trust it."""
    return send_file(auth_manager.cert_as_binary(), as_attachment=True, download_name='cert.pem')

@app.route('/')
def setup_main():
    """Renders the homepage or locked page"""
    if check_password():
        return render_template('setup.html')
    return render_template('locked.html')

@app.route('/1')
def setup_step1():
    """Renders the first setup page."""
    if check_password():
        return render_template('setup1.html')
    return render_template('locked.html')

@app.route('/2')
def setup_step2():
    """Renders the second setup page."""
    if check_password():
        return render_template('setup2.html')
    return render_template('locked.html')

@app.route('/3')
def setup_step3():
    """Renders the third setup page."""
    if check_password():
        return render_template('setup3.html')
    return render_template('locked.html')

@app.route('/4')
def setup_step4():
    """Renders the fourth setup page."""
    if check_password():
        return render_template('setup4.html')
    return render_template('locked.html')

@app.route('/5')
def setup_step5():
    """Renders the fifth setup page."""
    if check_password():
        return render_template('setup5.html')
    return render_template('locked.html')

@app.route('/6')
def setup_step6():
    """Renders the sixth setup page."""
    if check_password():
        return render_template('setup6.html')
    return render_template('locked.html')

@app.route('/7')
def setup_step7():
    """Renders the seventh setup page."""
    if check_password():
        return render_template('setup7.html')
    return render_template('locked.html')

@app.route('/8')
def setup_step8():
    """Renders the eighth setup page."""
    if check_password():
        return render_template('setup8.html')
    return render_template('locked.html')

@app.route('/9')
def setup_step9():
    """Renders the ninth setup page."""
    if check_password():
        return render_template('setup9.html')
    return render_template('locked.html')

@app.route('/calibrate')
def calibrate():
    """Renders the calibration page."""
    if check_password():
        return render_template('calibrate.html')
    return render_template('locked.html')

@app.route('/cert')
def cert():
    """Renders the certificate page."""
    if check_password():
        return render_template('cert.html')
    return render_template('locked.html')

@app.route('/contact')
def contact():
    """Renders the contact page."""
    if check_password():
        return render_template('contact.html')
    return render_template('locked.html')

@app.route('/done')
def done():
    """Renders the done page."""
    if check_password():
        return render_template('done.html')
    return render_template('locked.html')

@app.route('/rating')
def rating():
    """Renders the rating page."""
    if check_password():
        return render_template('rating.html')
    return render_template('locked.html')

@app.route('/start')
def start():
    """This is used for detecting if the information for both roomates has been captured. If it has, send to /calibrate, otherwise send to /1."""
    if check_password():
        #look at the cookies, if they have roomate_1 set to true and roomate_2 set to true, then go to /calibrate
        roomate_1 = request.cookies.get('roomate_1')
        roomate_2 = request.cookies.get('roomate_2')
        if roomate_1 == 'true' and roomate_2 == 'true':
            return redirect('/calibrate')
        return redirect('/1')
    
    return render_template('locked.html')

if __name__ == '__main__':
    app.run(ssl_context=('/home/pi/Desktop/webserver/ssl_keys/cert.pem', '/home/pi/Desktop/webserver/ssl_keys/key.pem'), host='0.0.0.0', port=5001)