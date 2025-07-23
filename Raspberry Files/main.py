#!/usr/bin/env python3
"""
Smart Vehicle Main Control System
Integrates all subsystems for autonomous navigation with Android app monitoring
"""

import time
import signal
import sys
from core.vision_system import NavigationVisionSystem
from core.motor_controller import MotorController
from core.sensor_manager import SensorManager
from core.navigation_ai import NavigationAI
from communication.protocol_manager import ProtocolManager
from utils.config_manager import ConfigManager
from utils.logger import Logger
from utils.performance_monitor import PerformanceMonitor

class SmartVehicle:
    def __init__(self):
        print("Initializing Smart Vehicle System...")
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize logger
        log_config = self.config_manager.get_config('logging')
        self.logger = Logger('SmartVehicle', log_config)
        self.logger.log_info("Smart Vehicle system starting up")
        
        # Initialize performance monitor
        perf_config = self.config_manager.get_config('performance')
        self.performance_monitor = PerformanceMonitor(perf_config)
        
        # Initialize core systems
        self.vision_system = None
        self.motor_controller = None
        self.sensor_manager = None
        self.navigation_ai = None
        self.protocol_manager = None
        
        # System state
        self.running = False
        self.auto_mode = False
        self.manual_override = False
        self.emergency_stop = False
        
        # Performance tracking
        self.loop_count = 0
        self.start_time = time.time()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("Smart Vehicle initialized successfully")
    
    def initialize_subsystems(self):
        """Initialize all vehicle subsystems"""
        try:
            self.logger.log_info("Initializing subsystems...")
            
            # Initialize vision system
            vision_config = self.config_manager.get_config('vision')
            android_config = self.config_manager.get_config('communication', 'android_app')
            
            self.vision_system = NavigationVisionSystem(
                camera_id=vision_config['camera_id'],
                resolution=tuple(vision_config['resolution']),
                android_streaming=android_config['video_streaming']['enabled']
            )
            self.logger.log_info("Vision system initialized")
            
            # Initialize motor controller
            self.motor_controller = MotorController()
            self.logger.log_info("Motor controller initialized")
            
            # Initialize sensor manager
            self.sensor_manager = SensorManager()
            self.sensor_manager.initialize_sensors()
            self.logger.log_info("Sensor manager initialized")
            
            # Initialize navigation AI
            self.navigation_ai = NavigationAI()
            self.logger.log_info("Navigation AI initialized")
            
            # Initialize communication protocols
            wifi_config = self.config_manager.get_config('communication', 'wifi')
            ble_config = self.config_manager.get_config('communication', 'ble')
            self.protocol_manager = ProtocolManager(wifi_config, ble_config)
            self.protocol_manager.initialize_protocols()
            
            # Start Android app services
            self.protocol_manager.start_android_app_service()
            self.logger.log_info("Communication protocols and Android app services initialized")
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            # Add performance alert callback
            self.performance_monitor.add_alert_callback(self._handle_performance_alert)
            
            # Send initialization status to Android app
            self._send_system_status("INITIALIZED", "All subsystems initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.log_exception(e, "Failed to initialize subsystems")
            return False
    
    def start(self):
        """Start the smart vehicle main loop"""
        if not self.initialize_subsystems():
            print("Failed to initialize subsystems. Exiting.")
            return False
        
        self.running = True
        self.logger.log_info("Smart Vehicle main loop starting")
        
        try:
            self._main_loop()
        except Exception as e:
            self.logger.log_exception(e, "Error in main loop")
        finally:
            self.shutdown()
        
        return True
    
    def _main_loop(self):
        """Main control loop"""
        while self.running:
            loop_start_time = time.time()
            
            try:
                # Update performance counter
                self.performance_monitor.update_fps()
                
                # Get sensor data
                sensor_data = self.sensor_manager.read_sensor_data()
                
                # Process vision (get frame and analyze)
                ret, frame = self.vision_system.camera.read()
                if not ret:
                    self.logger.log_warning("Failed to capture camera frame")
                    continue
                
                # Process navigation frame
                nav_output, navigation_data = self.vision_system.process_navigation_frame(frame)
                
                # Send video frame to Android app if streaming enabled
                android_config = self.config_manager.get_config('communication', 'android_app')
                if android_config['video_streaming']['enabled']:
                    stream_frame = self.vision_system.get_stream_frame()
                    if stream_frame is not None:
                        self.protocol_manager.send_video_frame(
                            stream_frame, 
                            android_config['video_streaming']['default_quality']
                        )
                
                # Get comprehensive vision data
                vision_data = navigation_data
                
                # Check for emergency conditions
                if self._check_emergency_conditions(sensor_data):
                    self._handle_emergency_stop()
                    continue
                
                # Process navigation decision if in auto mode
                if self.auto_mode and not self.manual_override:
                    decision = self.navigation_ai.process_navigation(vision_data, sensor_data)
                    self._execute_navigation_decision(decision)
                    
                    # Log navigation decision
                    self.logger.log_navigation_decision(decision, {
                        'vision': vision_data,
                        'sensors': sensor_data
                    })
                
                # Send telemetry to Android app
                self._send_telemetry_data(vision_data, sensor_data)
                
                # Send motor status to Android app
                motor_status = self.motor_controller.get_motor_status()
                self.protocol_manager.send_motor_status(motor_status)
                
                # Send system metrics periodically
                if self.loop_count % 100 == 0:  # Every 5 seconds at 20Hz
                    performance_data = self.performance_monitor.get_current_metrics()
                    self.protocol_manager.send_system_metrics(performance_data)
                
                # Handle incoming commands from Android app
                self._process_app_commands()
                
                # Update loop counter
                self.loop_count += 1
                
                # Maintain target loop frequency (20 Hz)
                loop_duration = time.time() - loop_start_time
                target_duration = 0.05  # 50ms for 20 Hz
                if loop_duration < target_duration:
                    time.sleep(target_duration - loop_duration)
                
            except Exception as e:
                self.logger.log_exception(e, "Error in main loop iteration")
                time.sleep(0.1)  # Brief pause before retrying
    
    def _check_emergency_conditions(self, sensor_data):
        """Check for emergency conditions that require immediate stop"""
        # Obstacle too close
        if sensor_data['obstacle_detected'] and sensor_data['distance'] < 15:
            return True
        
        # System overheating
        performance_data = self.performance_monitor.get_current_metrics()
        if performance_data['temperature'] > 75:  # Critical temperature
            return True
        
        return False
    
    def _handle_emergency_stop(self):
        """Handle emergency stop condition"""
        if not self.emergency_stop:
            self.emergency_stop = True
            self.motor_controller.all_motors_stop()
            self.logger.log_critical("EMERGENCY STOP ACTIVATED")
            
            # Send emergency alert to Android app
            self._send_alert("EMERGENCY_STOP", "critical", "Emergency stop activated due to safety conditions")
    
    def _execute_navigation_decision(self, decision):
        """Execute navigation decision through enhanced motor control"""
        if self.emergency_stop:
            return
        
        action = decision['action']
        speed = decision.get('speed', 0)
        
        # Prepare command for motor controller
        command_data = {
            'action': self._map_navigation_to_motor_action(action),
            'speed': speed,
            'source': 'autonomous',
            'turn_type': self._determine_turn_type(action)
        }
        
        try:
            success = self.motor_controller.execute_android_command(command_data)
            
            if success:
                # Log successful motor action
                self.logger.log_motor_action(action, {
                    'speed': speed, 
                    'reason': decision.get('reason', 'N/A'),
                    'success': True
                })
                
                # Send navigation update to Android app
                self.protocol_manager.send_navigation_update(
                    action, 
                    decision.get('filtered', False),
                    self.emergency_stop
                )
            else:
                self.logger.log_error(f"Failed to execute navigation decision: {action}")
            
        except Exception as e:
            self.logger.log_exception(e, f"Failed to execute navigation decision: {action}")
    
    def _map_navigation_to_motor_action(self, nav_action):
        """Map navigation actions to motor controller actions"""
        action_map = {
            'MOVE_FORWARD': 'forward',
            'TURN_LEFT': 'left',
            'TURN_RIGHT': 'right',
            'SHARP_LEFT': 'left',
            'SHARP_RIGHT': 'right',
            'STOP': 'stop',
            'EMERGENCY_STOP': 'emergency_stop'
        }
        return action_map.get(nav_action, 'stop')
    
    def _determine_turn_type(self, nav_action):
        """Determine turn type based on navigation action"""
        if 'SHARP' in nav_action:
            return 'sharp'
        elif 'TURN' in nav_action:
            return 'normal'
        else:
            return 'normal'
    
    def _send_telemetry_data(self, vision_data, sensor_data):
        """Send telemetry data to Android app"""
        try:
            # Get navigation status
            nav_status = self.navigation_ai.get_navigation_status()
            
            # Get performance metrics
            performance_data = self.performance_monitor.get_current_metrics()
            
            # Prepare telemetry package
            telemetry = {
                'timestamp': time.time(),
                'system_status': {
                    'running': self.running,
                    'auto_mode': self.auto_mode,
                    'manual_override': self.manual_override,
                    'emergency_stop': self.emergency_stop
                },
                'vision': vision_data,
                'sensors': sensor_data,
                'navigation': nav_status,
                'performance': {
                    'cpu_percent': performance_data['cpu_percent'],
                    'memory_percent': performance_data['memory_percent'],
                    'temperature': performance_data['temperature'],
                    'fps': performance_data['fps']
                },
                'runtime_stats': {
                    'uptime': time.time() - self.start_time,
                    'loop_count': self.loop_count
                }
            }
            
            # Send via protocol manager
            self.protocol_manager.send_telemetry(vision_data, sensor_data, nav_status)
            
        except Exception as e:
            self.logger.log_exception(e, "Failed to send telemetry data")
    
    def _process_app_commands(self):
        """Process incoming commands from Android app"""
        try:
            message, protocol = self.protocol_manager.receive_message()
            if message:
                self._handle_app_command(message, protocol)
        except Exception as e:
            self.logger.log_exception(e, "Error processing app commands")
    
    def _handle_app_command(self, message, protocol):
        """Handle specific command from Android app"""
        try:
            command_type = message.get('type', 'unknown')
            payload = message.get('payload', {})
            
            self.logger.log_communication_event(protocol, 'command_received', {
                'command_type': command_type,
                'payload': payload
            })
            
            if command_type == 'SET_AUTO_MODE':
                self.auto_mode = payload.get('enabled', False)
                self.logger.log_info(f"Auto mode {'enabled' if self.auto_mode else 'disabled'}")
                
            elif command_type == 'MANUAL_OVERRIDE':
                self.manual_override = payload.get('enabled', False)
                if self.manual_override:
                    self.motor_controller.all_motors_stop()
                self.logger.log_info(f"Manual override {'enabled' if self.manual_override else 'disabled'}")
                
            elif command_type == 'EMERGENCY_STOP':
                self._handle_emergency_stop()
                
            elif command_type == 'RESET_EMERGENCY':
                self.emergency_stop = False
                self.logger.log_info("Emergency stop reset")
                
            elif command_type == 'MANUAL_CONTROL':
                if self.manual_override:
                    self._handle_manual_control(payload)
                
            elif command_type == 'GET_STATUS':
                self._send_system_status("RUNNING", "System operational")
                
            elif command_type == 'UPDATE_CONFIG':
                self._handle_config_update(payload)
                
            elif command_type == 'GET_LOGS':
                self._handle_log_request(payload)
                
            elif command_type == 'STREAM_CONTROL':
                self._handle_stream_control(payload)
            
            # Send acknowledgment
            ack_message = {
                'type': 'COMMAND_ACK',
                'original_command': command_type,
                'status': 'processed',
                'timestamp': time.time()
            }
            self.protocol_manager.send_message(ack_message)
            
        except Exception as e:
            self.logger.log_exception(e, f"Error handling app command: {message}")
    
    def _handle_manual_control(self, payload):
        """Handle manual control commands from Android app"""
        if not self.manual_override or self.emergency_stop:
            return
        
        # Prepare command data for enhanced motor controller
        command_data = {
            'action': payload.get('action', 'stop'),
            'speed': payload.get('speed', 50),
            'duration': payload.get('duration', 0.5),
            'turn_type': payload.get('turn_type', 'normal'),
            'source': 'manual'
        }
        
        try:
            success = self.motor_controller.execute_android_command(command_data)
            
            if success:
                self.logger.log_android_command('manual_control', command_data, {'success': True})
            else:
                self.logger.log_android_command('manual_control', command_data, {'success': False})
            
        except Exception as e:
            self.logger.log_exception(e, f"Error in manual control: {command_data}")
    
    def _handle_config_update(self, payload):
        """Handle configuration updates from Android app"""
        try:
            section = payload.get('section')
            updates = payload.get('updates', {})
            
            if section == 'android_app':
                # Handle Android app specific configuration
                success = self.config_manager.update_android_app_config(updates)
                if success:
                    self.config_manager.save_config()
                    self.logger.log_android_command('config_update', payload, {'success': True})
                    self._send_system_status("CONFIG_UPDATED", "Android app configuration updated")
                else:
                    self.logger.log_android_command('config_update', payload, {'success': False})
            elif section and updates:
                self.config_manager.update_config(section, updates)
                self.config_manager.save_config()
                self.logger.log_android_command('config_update', payload, {'success': True})
                
                # Send confirmation
                self._send_system_status("CONFIG_UPDATED", f"Configuration section '{section}' updated")
        
        except Exception as e:
            self.logger.log_exception(e, "Error updating configuration")
    
    def _handle_log_request(self, payload):
        """Handle log request from Android app"""
        try:
            log_type = payload.get('type', 'recent')
            count = payload.get('count', 50)
            level_filter = payload.get('level_filter')
            
            if log_type == 'recent':
                logs = self.logger.get_recent_logs(count, level_filter)
            elif log_type == 'export':
                export_path = self.logger.export_logs_for_android()
                logs = {'export_path': export_path}
            else:
                logs = self.logger.get_log_stats()
            
            # Send logs to Android app
            log_response = {
                'type': 'log_data',
                'timestamp': time.time(),
                'log_type': log_type,
                'data': logs
            }
            
            self.protocol_manager.send_message(log_response, message_type='log_response')
            self.logger.log_android_command('log_request', payload, {'success': True})
            
        except Exception as e:
            self.logger.log_exception(e, "Error handling log request")
    
    def _handle_stream_control(self, payload):
        """Handle video stream control from Android app"""
        try:
            action = payload.get('action', 'status')
            
            if action == 'start':
                android_config = self.config_manager.get_config('communication', 'android_app')
                android_config['video_streaming']['enabled'] = True
                self.config_manager.set_config('communication', 'android_app', android_config)
                result = {'success': True, 'message': 'Video streaming started'}
                
            elif action == 'stop':
                android_config = self.config_manager.get_config('communication', 'android_app')
                android_config['video_streaming']['enabled'] = False
                self.config_manager.set_config('communication', 'android_app', android_config)
                result = {'success': True, 'message': 'Video streaming stopped'}
                
            elif action == 'quality':
                quality = payload.get('quality', 80)
                android_config = self.config_manager.get_config('communication', 'android_app')
                android_config['video_streaming']['default_quality'] = quality
                self.config_manager.set_config('communication', 'android_app', android_config)
                result = {'success': True, 'message': f'Video quality set to {quality}'}
                
            else:
                android_config = self.config_manager.get_config('communication', 'android_app')
                result = {
                    'success': True,
                    'status': android_config['video_streaming']
                }
            
            self.logger.log_android_command('stream_control', payload, result)
            
        except Exception as e:
            self.logger.log_exception(e, "Error handling stream control")
    
    def _send_system_status(self, status, message):
        """Send comprehensive system status update to Android app"""
        try:
            # Get comprehensive system information
            motor_status = self.motor_controller.get_motor_status() if self.motor_controller else {}
            performance_data = self.performance_monitor.get_current_metrics() if self.performance_monitor else {}
            protocol_status = self.protocol_manager.get_protocol_status() if self.protocol_manager else {}
            config_summary = self.config_manager.get_config_summary() if self.config_manager else {}
            
            status_data = {
                'type': 'system_status',
                'status': status,
                'message': message,
                'timestamp': time.time(),
                'system_info': {
                    'auto_mode': self.auto_mode,
                    'manual_override': self.manual_override,
                    'emergency_stop': self.emergency_stop,
                    'uptime': time.time() - self.start_time,
                    'loop_count': self.loop_count
                },
                'motor_status': motor_status,
                'performance': performance_data,
                'communication': protocol_status,
                'configuration': config_summary
            }
            
            self.protocol_manager.send_message(status_data, message_type='status')
            self.logger.log_android_command('system_status', {'status': status}, {'sent': True})
            
        except Exception as e:
            self.logger.log_exception(e, "Error sending system status")
    
    def _send_alert(self, alert_type, severity, message):
        """Send alert to Android app"""
        try:
            self.protocol_manager.send_alert(f"{alert_type}: {message}", severity)
        except Exception as e:
            self.logger.log_exception(e, "Error sending alert")
    
    def _handle_performance_alert(self, alert):
        """Handle performance monitoring alerts"""
        self.logger.log_warning(f"Performance Alert: {alert['message']}")
        
        # Send to Android app if critical
        if alert['type'] in ['temperature_high', 'cpu_high']:
            self._send_alert(alert['type'], 'warning', alert['message'])
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.log_info(f"Received signal {signum}, initiating shutdown")
        self.running = False
    
    def shutdown(self):
        """Graceful shutdown of all systems"""
        print("Shutting down Smart Vehicle...")
        self.logger.log_info("Smart Vehicle shutdown initiated")
        
        try:
            # Stop all motors
            if self.motor_controller:
                self.motor_controller.all_motors_stop()
                self.motor_controller.cleanup()
            
            # Stop vision system
            if self.vision_system:
                self.vision_system.cleanup()
            
            # Cleanup sensors
            if self.sensor_manager:
                self.sensor_manager.cleanup()
            
            # Stop performance monitoring
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
            
            # Cleanup communication
            if self.protocol_manager:
                self.protocol_manager.cleanup()
            
            # Final log
            self.logger.log_info("Smart Vehicle shutdown completed")
            self.logger.cleanup()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
        
        print("Smart Vehicle shutdown complete")

def main():
    """Main entry point"""
    print("Smart Vehicle Control System v1.0")
    print("Integrated Navigation and Android App Monitoring")
    print("Press Ctrl+C to stop")
    
    # Create and start the smart vehicle
    vehicle = SmartVehicle()
    success = vehicle.start()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())