//THIS FILE IS NO LONGER USED!
//The original device was controlled by an arduino and recieved serial commands for the door lock and handle servo
//This is now integrated into the RPI instead to remove the need for an arduino to reduce cost.

#include <Servo.h>

Servo handleServo;  // create servo object to control a servo
Servo lockServo;

const int trigPin = 9;
const int echoPin = 10;

float previousDistance = 0.0; // Initialize previous distance to 0

float distance_calibration = 0;
const int calibration_count = 15;
float calibration_values[calibration_count];

bool filter_activated = false;
int filter_activated_counter = 0;
const int filter_activated_threshold = 15; //The filter must be deactivated for 5 consecutive readings to deactivate the filter

float duration, distance;

float getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  return (duration * 0.0343) / 2;
}

void lockDoor() {
  lockServo.write(0);
  delay(800);
  lockServo.write(90);
  delay(800);
  lockServo.write(50);
  delay(800);
  lockServo.write(90);
  delay(800);
  lockServo.write(50);
  delay(800);
  lockServo.write(0);
}

void unlockDoor() {
  handleServo.write(0);
  delay(2500);
  handleServo.write(180);
  delay(2500);
  handleServo.write(0);
}

void setup() {
  handleServo.attach(2); //attatch the servo that opens the handle to pin 2
  lockServo.attach(3); //attatch the servo that locks the door to pin 3


  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  Serial.begin(9600);

  Serial.println("Calibrating...");
  for (int i = 0; i < calibration_count; i++) {
    calibration_values[i] = getDistance();
    //Serial.println("(" + i + " / " + calibration_count + ") Value: " + calibration_values[i]);
    Serial.println(" ");
    Serial.print("(");
    Serial.print(i);
    Serial.print(" / ");
    Serial.print(calibration_count);
    Serial.print(") Value: ");
    Serial.println(calibration_values[i]);
    delay(100);
  }
  // Calculate the average of the calibration values
  Serial.println("Calculating average...");
  for (int i = 0; i < calibration_count; i++) {
    distance_calibration += calibration_values[i];
  }
  distance_calibration /= calibration_count;
  Serial.println(" ");
  Serial.print("Calibration complete. Average: ");
  Serial.print(distance_calibration);
  Serial.println(" ");

  Serial.println("Calibrating the door lock system...");
  lockDoor();
  delay(1000);
  unlockDoor();
  delay(1000);
  Serial.println("Calibration complete.");
}

void loop() {
  float distance = getDistance();
  Serial.print("Distance: ");
  Serial.println(distance);
  if ((distance > distance_calibration + 5 || distance < distance_calibration - 5)) {
    Serial.println("Activated filter");
    filter_activated = true;
    filter_activated_counter = 0;
  } else {
    filter_activated_counter++;
    if (filter_activated_counter >= filter_activated_threshold && filter_activated) {
      Serial.println("Deactivated filter");
      filter_activated = false;
      filter_activated_counter = 0;
      delay(5000); // Wait 5 seconds before locking because sometimes the door is not fully closed
      lockDoor();
    }
    previousDistance = distance;
  }
  delay(100);
}