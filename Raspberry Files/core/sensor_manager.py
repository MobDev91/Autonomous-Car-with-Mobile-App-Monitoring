#!/usr/bin/env python3
"""
Sensor Manager Module
Manages ultrasonic sensor for obstacle detection and distance measurement
"""

import RPi.GPIO as GPIO
import time

class SensorManager:
    def __init__(self):
        # Pin setup for HC-SR04 ultrasonic sensor
        self.TRIG = 27  # GPIO27 - Pin 13
        self.ECHO = 26  # GPIO26 - Pin 37
        
        # Obstacle detection threshold (cm)
        self.obstacle_threshold = 20
        
        self._setup_gpio()
        
    def _setup_gpio(self):
        """Set up GPIO pins for ultrasonic sensor"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)
        
        # Initialize ultrasonic sensor
        GPIO.output(self.TRIG, GPIO.LOW)
        time.sleep(0.1)  # Allow sensor to settle
    
    def initialize_sensors(self):
        """Initialize all sensors"""
        print("Sensors initialized successfully")
        return True
    
    def get_distance(self):
        """Get distance from ultrasonic sensor in cm"""
        # Send 10us trigger pulse
        GPIO.output(self.TRIG, GPIO.HIGH)
        time.sleep(0.00001)  # 10 microseconds
        GPIO.output(self.TRIG, GPIO.LOW)

        # Wait for echo start
        pulse_start = time.time()
        timeout = pulse_start + 0.1  # 100ms timeout
        while GPIO.input(self.ECHO) == 0:
            pulse_start = time.time()
            if pulse_start > timeout:
                return 400  # Return max distance if timeout

        # Wait for echo end
        pulse_end = time.time()
        timeout = pulse_end + 0.1  # 100ms timeout
        while GPIO.input(self.ECHO) == 1:
            pulse_end = time.time()
            if pulse_end > timeout:
                return 400  # Return max distance if timeout

        # Calculate distance (speed of sound = 343m/s = 0.0343cm/us)
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # (34300 cm/s) / 2
        return round(distance, 2)
    
    def read_sensor_data(self):
        """Read data from all sensors"""
        distance = self.get_distance()
        obstacle_detected = distance < self.obstacle_threshold
        
        return {
            'distance': distance,
            'obstacle_detected': obstacle_detected,
            'obstacle_threshold': self.obstacle_threshold
        }
    
    def check_obstacle(self):
        """Check if there's an obstacle in front of the car"""
        distance = self.get_distance()
        return distance < self.obstacle_threshold, distance
    
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()