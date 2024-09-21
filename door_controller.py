from time import sleep
import time
import threading

import RPi.GPIO as GPIO 

class DoorController:
    def __init__(self, calibrate_silent=True):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self.ULT_TRIGGER = 4
        self.ULT_ECHO = 17

        GPIO.setup(23, GPIO.OUT) #LOCKING SERVO
        GPIO.setup(24, GPIO.OUT) #HANDLE SERVO

        GPIO.setup(self.ULT_TRIGGER, GPIO.OUT) #Ultrasonic TRIGGER
        GPIO.setup(self.ULT_ECHO, GPIO.IN) #Ultrasonic ECHO

        self.lockingServo = GPIO.PWM(23, 50)
        self.handleServo = GPIO.PWM(24, 50)
        
        self.lockingServo.start(0)
        self.handleServo.start(0)

        self.calibration_count = 10
        self.calibration_average = 0

        self.filter_activated_cache = False

        self.runCalibration(calibrate_silent)

        self.filter_activated_counter = 0
        self.filter_activated = False


    def getDistance(self):
        GPIO.output(self.ULT_TRIGGER, True)
    
        time.sleep(0.00001)
        GPIO.output(self.ULT_TRIGGER, False)
    
        StartTime = time.time()
        StopTime = time.time()
    
        while GPIO.input(self.ULT_ECHO) == 0:
            StartTime = time.time()
    
        while GPIO.input(self.ULT_ECHO) == 1:
            StopTime = time.time()
    
        TimeElapsed = StopTime - StartTime
        distance = (TimeElapsed * 34300) / 2
 
        return distance

    def lock(self):
        self.lockingServo.ChangeDutyCycle(1)
        sleep(0.8)
        self.lockingServo.ChangeDutyCycle(8)
        sleep(0.8)
        self.lockingServo.ChangeDutyCycle(5)
        sleep(0.8)
        self.lockingServo.ChangeDutyCycle(8)
        sleep(0.8)
        self.lockingServo.ChangeDutyCycle(1)

    def unlock(self):
        self.handleServo.ChangeDutyCycle(1)
        sleep(2.5)
        self.handleServo.ChangeDutyCycle(12)
        sleep(2.5)
        self.handleServo.ChangeDutyCycle(1)
        threading.Thread(target=self.start_relock_timer).start()
    
    def start_relock_timer(self):
        for x in range(8):
            print("Relock in " + str(8 - x) + " seconds")
            sleep(1)
        print("Relock status: " + str(self.filter_activated_cache))
        if not self.filter_activated_cache:
            self.lock()
        self.filter_activated_cache = False

    def runCalibration(self, silent):
        calibration_values = []
        for i in range(self.calibration_count):
            calibration_values.append(self.getDistance())
            print(" ")
            print("(" + str(i) + " / " + str(self.calibration_count) + ") Value: " + str(calibration_values[i]))
            sleep(0.1)

        #Calculate average
        s = 0
        for i in range(self.calibration_count):
            s += calibration_values[i]
        average = s / self.calibration_count
        print(" ")
        print("Average: " + str(average))
        self.calibration_average = average

        if silent:
            print("Skipping lock calibration...")
        else:
            print("Calibrating lock system...")
            self.lock()
            sleep(1)
            self.unlock()
            sleep(1)
    
    def main_loop_single_runnable(self):
        distance = self.getDistance()
        if distance > self.calibration_average + 5 or distance < self.calibration_average - 5:
            print("Activated filter", flush=True)
            self.filter_activated = True
            self.filter_activated_counter = 0
            self.filter_activated_cache = True
        else:
            self.filter_activated_counter += 1
            if self.filter_activated_counter >= 5 and self.filter_activated:
                print("Deactivated filter", flush=True)
                self.filter_activated = False
                self.filter_activated_cache = False
                self.filter_activated_counter = 0
                sleep(5)
                self.lock()
            
        return True

    def setLockAngle(self, angle): #This is for DEBUG!
        self.lockingServo.ChangeDutyCycle(angle)

    def setHandleAngle(self, angle): #This is for DEBUG
        self.handleServo.ChangeDutyCycle(angle)
