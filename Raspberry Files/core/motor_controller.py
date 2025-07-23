#!/usr/bin/env python3
"""
Advanced Motor Control Module for Smart Vehicle
Controls 4 motors via dual L298N motor drivers with Android app integration,
smooth acceleration/deceleration, and comprehensive safety features.
"""

import RPi.GPIO as GPIO
import time

class MotorController:
    def __init__(self, config=None):
        # Pin setup for first L298N (Motors 1 and 2) - Front wheels
        self.IN1 = 17  # GPIO17 - Pin 11 - Front Left Forward
        self.IN2 = 22  # GPIO22 - Pin 15 - Front Left Backward  
        self.IN3 = 23  # GPIO23 - Pin 16 - Front Right Forward
        self.IN4 = 24  # GPIO24 - Pin 18 - Front Right Backward
        self.ENA = 18  # GPIO18 - Pin 12 (PWM for Front Left Motor)
        self.ENB = 25  # GPIO25 - Pin 22 (PWM for Front Right Motor)

        # Pin setup for second L298N (Motors 3 and 4) - Rear wheels
        self.IN5 = 5   # GPIO5  - Pin 29 - Rear Left Forward
        self.IN6 = 6   # GPIO6  - Pin 31 - Rear Left Backward
        self.IN7 = 13  # GPIO13 - Pin 33 - Rear Right Forward
        self.IN8 = 19  # GPIO19 - Pin 35 - Rear Right Backward
        self.ENC = 12  # GPIO12 - Pin 32 (PWM for Rear Left Motor)
        self.END = 16  # GPIO16 - Pin 36 (PWM for Rear Right Motor)
        
        # Initialize GPIO
        self._setup_gpio()
        
        # Speed settings
        self.default_speed = 75
        self.current_speed = 0
        self.max_speed = 100
        self.min_speed = 20
        
        # Smooth acceleration settings
        self.acceleration_step = 5
        self.acceleration_delay = 0.05  # 50ms between steps
        self.smooth_control = True
        
        # Motor state tracking for Android app
        self.motor_state = {
            'front_left': {'speed': 0, 'direction': 'stop'},
            'front_right': {'speed': 0, 'direction': 'stop'},
            'rear_left': {'speed': 0, 'direction': 'stop'},
            'rear_right': {'speed': 0, 'direction': 'stop'},
            'current_action': 'stopped',
            'target_speed': 0,
            'actual_speed': 0
        }
        
        # Safety features
        self.emergency_stop_active = False
        self.last_command_time = time.time()
        self.command_timeout = 2.0  # Stop if no command for 2 seconds
        
        # Performance tracking
        self.total_distance = 0  # Estimated distance traveled
        self.runtime_stats = {
            'total_commands': 0,
            'emergency_stops': 0,
            'manual_overrides': 0,
            'autonomous_commands': 0
        }
        
    def _setup_gpio(self):
        """Set up GPIO pins for motors and ultrasonic sensor"""
        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.IN1, self.IN2, self.IN3, self.IN4, self.IN5, self.IN6, self.IN7, self.IN8], GPIO.OUT)
        GPIO.setup([self.ENA, self.ENB, self.ENC, self.END], GPIO.OUT)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)

        # PWM setup (50Hz for L298N)
        self.pwm1 = GPIO.PWM(self.ENA, 50)  # Motor 1
        self.pwm2 = GPIO.PWM(self.ENB, 50)  # Motor 2
        self.pwm3 = GPIO.PWM(self.ENC, 50)  # Motor 3
        self.pwm4 = GPIO.PWM(self.END, 50)  # Motor 4
        self.pwm1.start(0)
        self.pwm2.start(0)
        self.pwm3.start(0)
        self.pwm4.start(0)
        
        # Initialize ultrasonic sensor
        GPIO.output(self.TRIG, GPIO.LOW)
        time.sleep(0.1)  # Allow sensor to settle

    # Motor control functions
    def motor1_forward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        self.pwm1.ChangeDutyCycle(speed)

    def motor1_backward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.HIGH)
        self.pwm1.ChangeDutyCycle(speed)

    def motor1_stop(self):
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.LOW)
        self.pwm1.ChangeDutyCycle(0)

    def motor2_forward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN3, GPIO.HIGH)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwm2.ChangeDutyCycle(speed)

    def motor2_backward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.HIGH)
        self.pwm2.ChangeDutyCycle(speed)

    def motor2_stop(self):
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwm2.ChangeDutyCycle(0)

    def motor3_forward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN5, GPIO.HIGH)
        GPIO.output(self.IN6, GPIO.LOW)
        self.pwm3.ChangeDutyCycle(speed)

    def motor3_backward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN5, GPIO.LOW)
        GPIO.output(self.IN6, GPIO.HIGH)
        self.pwm3.ChangeDutyCycle(speed)

    def motor3_stop(self):
        GPIO.output(self.IN5, GPIO.LOW)
        GPIO.output(self.IN6, GPIO.LOW)
        self.pwm3.ChangeDutyCycle(0)

    def motor4_forward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN7, GPIO.HIGH)
        GPIO.output(self.IN8, GPIO.LOW)
        self.pwm4.ChangeDutyCycle(speed)

    def motor4_backward(self, speed=None):
        if speed is None:
            speed = self.default_speed
        GPIO.output(self.IN7, GPIO.LOW)
        GPIO.output(self.IN8, GPIO.HIGH)
        self.pwm4.ChangeDutyCycle(speed)

    def motor4_stop(self):
        GPIO.output(self.IN7, GPIO.LOW)
        GPIO.output(self.IN8, GPIO.LOW)
        self.pwm4.ChangeDutyCycle(0)

    # Advanced motor control functions with Android app integration
    def all_motors_forward(self, speed=None, smooth=None):
        """Move all motors forward with optional smooth acceleration"""
        if self.emergency_stop_active:
            return False
            
        if speed is None:
            speed = self.default_speed
        
        smooth = smooth if smooth is not None else self.smooth_control
        
        if smooth:
            return self._smooth_transition('forward', speed)
        else:
            self.motor1_forward(speed)  # Front Left
            self.motor2_forward(speed)  # Front Right  
            self.motor3_forward(speed)  # Rear Left
            self.motor4_forward(speed)  # Rear Right
            
        self._update_motor_state('forward', speed)
        self.runtime_stats['total_commands'] += 1
        return True

    def all_motors_backward(self, speed=None, smooth=None):
        """Move all motors backward with optional smooth acceleration"""
        if self.emergency_stop_active:
            return False
            
        if speed is None:
            speed = self.default_speed
            
        smooth = smooth if smooth is not None else self.smooth_control
        
        if smooth:
            return self._smooth_transition('backward', speed)
        else:
            self.motor1_backward(speed)
            self.motor2_backward(speed)
            self.motor3_backward(speed)
            self.motor4_backward(speed)
            
        self._update_motor_state('backward', speed)
        self.runtime_stats['total_commands'] += 1
        return True

    def all_motors_stop(self, immediate=False):
        """Stop all motors with optional smooth deceleration"""
        if immediate or not self.smooth_control:
            self.motor1_stop()
            self.motor2_stop()
            self.motor3_stop()
            self.motor4_stop()
            self.current_speed = 0
        else:
            self._smooth_transition('stop', 0)
            
        self._update_motor_state('stopped', 0)
        self.runtime_stats['total_commands'] += 1
        return True
        
    def turn_left(self, speed=None, turn_type='normal'):
        """Enhanced left turn with different turning modes"""
        if self.emergency_stop_active:
            return False
            
        if speed is None:
            speed = self.default_speed
            
        if turn_type == 'sharp':
            # Sharp left turn - left motors backward, right motors forward
            self.motor1_backward(speed)  # Front Left
            self.motor3_backward(speed)  # Rear Left
            self.motor2_forward(speed)   # Front Right
            self.motor4_forward(speed)   # Rear Right
        elif turn_type == 'pivot':
            # Pivot turn - left motors backward, right motors forward at higher speed
            pivot_speed = min(speed + 20, self.max_speed)
            self.motor1_backward(pivot_speed)
            self.motor3_backward(pivot_speed)
            self.motor2_forward(pivot_speed)
            self.motor4_forward(pivot_speed)
        else:  # normal turn
            # Gentle left turn - slow down left motors, maintain right motors
            left_speed = max(speed - 30, self.min_speed)
            self.motor1_forward(left_speed)  # Front Left slower
            self.motor3_forward(left_speed)  # Rear Left slower
            self.motor2_forward(speed)       # Front Right normal
            self.motor4_forward(speed)       # Rear Right normal
            
        self._update_motor_state(f'turn_left_{turn_type}', speed)
        self.runtime_stats['total_commands'] += 1
        return True
        
    def turn_right(self, speed=None, turn_type='normal'):
        """Enhanced right turn with different turning modes"""
        if self.emergency_stop_active:
            return False
            
        if speed is None:
            speed = self.default_speed
            
        if turn_type == 'sharp':
            # Sharp right turn - right motors backward, left motors forward
            self.motor2_backward(speed)  # Front Right
            self.motor4_backward(speed)  # Rear Right
            self.motor1_forward(speed)   # Front Left
            self.motor3_forward(speed)   # Rear Left
        elif turn_type == 'pivot':
            # Pivot turn - right motors backward, left motors forward at higher speed
            pivot_speed = min(speed + 20, self.max_speed)
            self.motor2_backward(pivot_speed)
            self.motor4_backward(pivot_speed)
            self.motor1_forward(pivot_speed)
            self.motor3_forward(pivot_speed)
        else:  # normal turn
            # Gentle right turn - slow down right motors, maintain left motors
            right_speed = max(speed - 30, self.min_speed)
            self.motor2_forward(right_speed)  # Front Right slower
            self.motor4_forward(right_speed)  # Rear Right slower
            self.motor1_forward(speed)        # Front Left normal
            self.motor3_forward(speed)        # Rear Left normal
            
        self._update_motor_state(f'turn_right_{turn_type}', speed)
        self.runtime_stats['total_commands'] += 1
        return True

    # Advanced control methods for Android app integration
    def _smooth_transition(self, target_action, target_speed):
        """Smooth transition between motor states"""
        if target_action == 'stop':
            # Gradual deceleration
            while self.current_speed > 0:
                self.current_speed = max(0, self.current_speed - self.acceleration_step)
                self._apply_speed_to_all_motors(self.current_speed)
                time.sleep(self.acceleration_delay)
            self.all_motors_stop(immediate=True)
            return True
        
        # Gradual acceleration/deceleration to target speed
        while abs(self.current_speed - target_speed) > self.acceleration_step:
            if self.current_speed < target_speed:
                self.current_speed = min(target_speed, self.current_speed + self.acceleration_step)
            else:
                self.current_speed = max(target_speed, self.current_speed - self.acceleration_step)
            
            if target_action == 'forward':
                self._apply_speed_to_all_motors(self.current_speed, 'forward')
            elif target_action == 'backward':
                self._apply_speed_to_all_motors(self.current_speed, 'backward')
                
            time.sleep(self.acceleration_delay)
        
        self.current_speed = target_speed
        return True
    
    def _apply_speed_to_all_motors(self, speed, direction='forward'):
        """Apply speed to all motors in specified direction"""
        if direction == 'forward':
            self.motor1_forward(speed)
            self.motor2_forward(speed)
            self.motor3_forward(speed)
            self.motor4_forward(speed)
        elif direction == 'backward':
            self.motor1_backward(speed)
            self.motor2_backward(speed)
            self.motor3_backward(speed)
            self.motor4_backward(speed)
    
    def _update_motor_state(self, action, speed):
        """Update motor state for Android app monitoring"""
        self.last_command_time = time.time()
        self.motor_state['current_action'] = action
        self.motor_state['target_speed'] = speed
        self.motor_state['actual_speed'] = self.current_speed
        
        # Update individual motor states based on action
        if 'forward' in action:
            direction = 'forward'
        elif 'backward' in action:
            direction = 'backward'
        elif 'stop' in action:
            direction = 'stop'
            speed = 0
        elif 'turn_left' in action:
            direction = 'turn_left'
        elif 'turn_right' in action:
            direction = 'turn_right'
        else:
            direction = 'unknown'
        
        for motor in self.motor_state:
            if motor != 'current_action' and motor != 'target_speed' and motor != 'actual_speed':
                if isinstance(self.motor_state[motor], dict):
                    self.motor_state[motor]['direction'] = direction
                    self.motor_state[motor]['speed'] = speed
    
    def emergency_stop(self):
        """Immediate emergency stop with safety lockout"""
        self.emergency_stop_active = True
        self.all_motors_stop(immediate=True)
        self.runtime_stats['emergency_stops'] += 1
        print("EMERGENCY STOP ACTIVATED")
        return True
    
    def reset_emergency_stop(self):
        """Reset emergency stop state"""
        self.emergency_stop_active = False
        print("Emergency stop reset - normal operation resumed")
        return True
    
    def execute_android_command(self, command_data):
        """Execute motor command from Android app"""
        try:
            action = command_data.get('action', 'stop')
            speed = command_data.get('speed', self.default_speed)
            duration = command_data.get('duration', 0)
            turn_type = command_data.get('turn_type', 'normal')
            source = command_data.get('source', 'unknown')
            
            # Validate parameters
            speed = max(self.min_speed, min(self.max_speed, speed))
            
            # Update statistics
            if source == 'manual':
                self.runtime_stats['manual_overrides'] += 1
            elif source == 'autonomous':
                self.runtime_stats['autonomous_commands'] += 1
            
            # Execute command
            success = False
            if action == 'forward':
                success = self.all_motors_forward(speed)
            elif action == 'backward':
                success = self.all_motors_backward(speed)
            elif action == 'left':
                success = self.turn_left(speed, turn_type)
            elif action == 'right':
                success = self.turn_right(speed, turn_type)
            elif action == 'stop':
                success = self.all_motors_stop()
            elif action == 'emergency_stop':
                success = self.emergency_stop()
            
            # Handle timed commands
            if success and duration > 0 and action != 'stop':
                time.sleep(duration)
                self.all_motors_stop()
            
            return success
            
        except Exception as e:
            print(f"Error executing Android command: {e}")
            self.all_motors_stop(immediate=True)
            return False
    
    def get_motor_status(self):
        """Get comprehensive motor status for Android app"""
        current_time = time.time()
        time_since_command = current_time - self.last_command_time
        
        # Auto-stop if no commands received for timeout period
        if time_since_command > self.command_timeout and not self.emergency_stop_active:
            if self.motor_state['current_action'] != 'stopped':
                self.all_motors_stop()
        
        return {
            'motor_state': self.motor_state.copy(),
            'emergency_stop_active': self.emergency_stop_active,
            'smooth_control_enabled': self.smooth_control,
            'time_since_last_command': time_since_command,
            'runtime_stats': self.runtime_stats.copy(),
            'speed_settings': {
                'current': self.current_speed,
                'default': self.default_speed,
                'max': self.max_speed,
                'min': self.min_speed
            }
        }
    
    def set_speed_parameters(self, default=None, max_speed=None, min_speed=None):
        """Update speed parameters from Android app"""
        if default is not None:
            self.default_speed = max(0, min(100, default))
        if max_speed is not None:
            self.max_speed = max(self.min_speed, min(100, max_speed))
        if min_speed is not None:
            self.min_speed = max(0, min(self.max_speed, min_speed))
        
        return True
    
    def enable_smooth_control(self, enabled=True):
        """Enable or disable smooth acceleration/deceleration"""
        self.smooth_control = enabled
        return True
    
    def cleanup(self):
        """Clean up GPIO resources"""
        print("Cleaning up motor controller...")
        self.all_motors_stop(immediate=True)
        
        # Stop PWM
        try:
            self.pwm1.stop()
            self.pwm2.stop()
            self.pwm3.stop()
            self.pwm4.stop()
        except:
            pass
        
        # Clean up GPIO
        try:
            GPIO.cleanup()
        except:
            pass
        
        print("Motor controller cleanup completed")

# Test code when run directly
if __name__ == "__main__":
    try:
        motor_controller = MotorController()
        print("Motor controller initialized")
        
        while True:
            # Measure distance
            distance = motor_controller.get_distance()
            print(f"Distance: {distance} cm")

            # Obstacle detection (stop if closer than threshold)
            if distance < motor_controller.obstacle_threshold:
                print("Obstacle detected! Stopping motors")
                motor_controller.all_motors_stop()
                time.sleep(1)  # Wait before next measurement
            else:
                print("Path clear, moving forward")
                motor_controller.all_motors_forward()  # Move forward at default speed
                time.sleep(0.1)  # Short delay to avoid overloading sensor

    except KeyboardInterrupt:
        print("Exiting program")

    finally:
        if 'motor_controller' in locals():
            motor_controller.cleanup()
