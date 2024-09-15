from gpiozero import DistanceSensor
ultrasonic = DistanceSensor(echo=17, trigger=4)
import time

while True:
    time.sleep(0.1)
    print(ultrasonic.distance)