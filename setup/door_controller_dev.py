#These are meant to run the tests inside of the calibrate page. Do not run them outside of the calibrate page.

from time import sleep
import time
import threading

import RPi.GPIO as GPIO 

class DoorControllerDEV:
    def __init__(self):
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
