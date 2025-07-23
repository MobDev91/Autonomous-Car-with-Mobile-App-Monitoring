#!/usr/bin/env python3
"""
Android App Communication Protocol Manager
Manages communication protocols optimized for Android app integration
with real-time telemetry streaming, command processing, and failover capabilities.
"""

import time
import json
from datetime import datetime
from .wifi_handler import WiFiHandler
from .ble_handler import BLEHandler

class ProtocolManager:
    def __init__(self, wifi_config=None, ble_config=None):
        # Initialize communication handlers
        if wifi_config:
            self.wifi_handler = WiFiHandler(
                server_ip=wifi_config.get('server_ip', '192.168.1.100'),
                server_port=wifi_config.get('server_port', 8080)
            )
        else:
            self.wifi_handler = WiFiHandler()
        
        if ble_config:
            self.ble_handler = BLEHandler(
                device_name=ble_config.get('device_name', 'SmartVehicle'),
                service_uuid=ble_config.get('service_uuid', '12345678-1234-1234-1234-123456789abc')
            )
        else:
            self.ble_handler = BLEHandler()
        
        # Protocol priority settings
        self.primary_protocol = 'wifi'  # 'wifi' or 'ble'
        self.fallback_enabled = True
        
        # Message tracking
        self.message_id_counter = 0
        self.sent_messages = {}
        
        print("Protocol Manager initialized")
    
    def initialize_protocols(self):
        """Initialize all communication protocols"""
        success_count = 0
        
        # Initialize WiFi
        if self.wifi_handler.connect_wifi():
            self.wifi_handler.start_auto_reconnect()
            success_count += 1
            print("WiFi protocol initialized successfully")
        else:
            print("WiFi protocol initialization failed")
        
        # Initialize BLE
        if self.ble_handler.start_advertising():
            success_count += 1
            print("BLE protocol initialized successfully")
        else:
            print("BLE protocol initialization failed")
        
        return success_count > 0
    
    def manage_protocols(self):
        """Manage protocol states and health"""
        wifi_status = self.wifi_handler.get_connection_status()
        ble_status = self.ble_handler.get_connection_status()
        
        protocol_status = {
            'wifi': {
                'connected': wifi_status['connected'],
                'buffered_messages': wifi_status['buffered_messages']
            },
            'ble': {
                'connected': ble_status['connected'],
                'advertising': ble_status['advertising'],
                'buffered_messages': ble_status['buffered_messages']
            },
            'primary_protocol': self.primary_protocol,
            'timestamp': datetime.now().isoformat()
        }
        
        # Switch primary protocol if needed
        if self.fallback_enabled:
            if self.primary_protocol == 'wifi' and not wifi_status['connected']:
                if ble_status['connected']:
                    print("Switching to BLE as primary protocol (WiFi disconnected)")
                    self.primary_protocol = 'ble'
            elif self.primary_protocol == 'ble' and not ble_status['connected']:
                if wifi_status['connected']:
                    print("Switching to WiFi as primary protocol (BLE disconnected)")
                    self.primary_protocol = 'wifi'
        
        return protocol_status
    
    def send_message(self, message, protocol=None, message_type='data'):
        """Send message using specified or primary protocol"""
        if protocol is None:
            protocol = self.primary_protocol
        
        # Generate message ID
        self.message_id_counter += 1
        message_id = f"msg_{self.message_id_counter}_{int(time.time())}"
        
        # Prepare message with metadata
        full_message = {
            'id': message_id,
            'type': message_type,
            'payload': message,
            'timestamp': datetime.now().isoformat(),
            'protocol': protocol
        }
        
        success = False
        
        # Send via primary protocol
        if protocol == 'wifi':
            success = self.wifi_handler.send_data(full_message)
        elif protocol == 'ble':
            success = self.ble_handler.transmit_data(full_message)
        
        # Fallback to secondary protocol if primary fails
        if not success and self.fallback_enabled:
            fallback_protocol = 'ble' if protocol == 'wifi' else 'wifi'
            print(f"Primary protocol ({protocol}) failed, trying fallback ({fallback_protocol})")
            
            full_message['protocol'] = fallback_protocol
            if fallback_protocol == 'wifi':
                success = self.wifi_handler.send_data(full_message)
            elif fallback_protocol == 'ble':
                success = self.ble_handler.transmit_data(full_message)
        
        # Track sent message
        if success:
            self.sent_messages[message_id] = {
                'message': full_message,
                'sent_at': datetime.now().isoformat(),
                'protocol_used': full_message['protocol']
            }
        
        return success, message_id
    
    def receive_message(self, protocol=None):
        """Receive message from specified or any protocol"""
        if protocol is None:
            # Try both protocols
            wifi_message = self.wifi_handler.receive_data()
            if wifi_message:
                return wifi_message, 'wifi'
            
            ble_message = self.ble_handler.receive_data()
            if ble_message:
                return ble_message, 'ble'
            
            return None, None
        
        elif protocol == 'wifi':
            message = self.wifi_handler.receive_data()
            return message, 'wifi' if message else None
        
        elif protocol == 'ble':
            message = self.ble_handler.receive_data()
            return message, 'ble' if message else None
        
        return None, None
    
    def handle_communication(self, data, priority='normal'):
        """Handle communication with Android app optimization"""
        protocol_status = self.manage_protocols()
        
        # Add Android app specific headers
        data['app_protocol_version'] = '1.0'
        data['device_id'] = 'smart_vehicle_001'
        
        # Determine best protocol based on data type and priority
        if data.get('type') == 'video_frame':
            # Video frames prefer WiFi for bandwidth
            if protocol_status['wifi']['connected']:
                success, msg_id = self.send_message(data, 'wifi', 'video')
                return success
            # Fallback to BLE with lower quality
            elif protocol_status['ble']['connected']:
                # Reduce video quality for BLE
                if 'frame_data' in data:
                    data['frame_data'] = data['frame_data'][:len(data['frame_data'])//4]  # Reduce size
                success, msg_id = self.send_message(data, 'ble', 'video')
                return success
        
        elif priority == 'high':
            # Critical commands (emergency stop, alerts)
            wifi_success, wifi_msg_id = self.send_message(data, 'wifi', 'critical')
            ble_success, ble_msg_id = self.send_message(data, 'ble', 'critical')
            return wifi_success or ble_success
        
        elif priority == 'low':
            # Non-critical data (metrics, logs)
            if protocol_status['wifi']['connected']:
                success, msg_id = self.send_message(data, 'wifi', 'background')
                return success
            elif protocol_status['ble']['connected'] and protocol_status['ble']['buffered_messages'] < 10:
                success, msg_id = self.send_message(data, 'ble', 'background')
                return success
        
        else:  # normal priority (telemetry, status)
            success, msg_id = self.send_message(data, None, 'normal')
            return success
        
        return False
    
    def send_telemetry(self, vision_data, sensor_data, navigation_data):
        """Send comprehensive telemetry data optimized for Android app"""
        telemetry = {
            'type': 'telemetry',
            'timestamp': time.time(),
            'vision': vision_data,
            'sensors': sensor_data,
            'navigation': navigation_data,
            'frame_id': int(time.time() * 1000) % 1000000  # Unique frame ID
        }
        
        return self.handle_communication(telemetry, 'normal')
    
    def send_video_frame(self, frame_data, quality=80):
        """Send video frame data to Android app"""
        if frame_data is None:
            return False
        
        try:
            import cv2
            import base64
            
            # Encode frame as JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, buffer = cv2.imencode('.jpg', frame_data, encode_param)
            
            # Convert to base64 for transmission
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            video_packet = {
                'type': 'video_frame',
                'timestamp': time.time(),
                'frame_data': frame_base64,
                'frame_size': len(buffer),
                'quality': quality
            }
            
            return self.handle_communication(video_packet, 'low')  # Low priority for video
            
        except Exception as e:
            print(f"Error sending video frame: {e}")
            return False
    
    def send_motor_status(self, motor_status):
        """Send motor status update to Android app"""
        status_packet = {
            'type': 'motor_status',
            'timestamp': time.time(),
            'motor_data': motor_status
        }
        
        return self.handle_communication(status_packet, 'normal')
    
    def send_system_metrics(self, performance_metrics):
        """Send system performance metrics to Android app"""
        metrics_packet = {
            'type': 'system_metrics',
            'timestamp': time.time(),
            'metrics': performance_metrics
        }
        
        return self.handle_communication(metrics_packet, 'low')
    
    def send_alert(self, alert_message, severity='warning'):
        """Send alert message optimized for Android app notifications"""
        alert = {
            'type': 'alert',
            'timestamp': time.time(),
            'alert_id': f"alert_{int(time.time() * 1000)}",
            'message': alert_message,
            'severity': severity,
            'requires_ack': severity in ['critical', 'error'],
            'auto_dismiss': severity in ['info', 'warning']
        }
        
        priority = 'high' if severity in ['critical', 'error'] else 'normal'
        return self.handle_communication(alert, priority)
    
    def send_navigation_update(self, direction, confidence, obstacles):
        """Send navigation update to Android app"""
        nav_update = {
            'type': 'navigation_update',
            'timestamp': time.time(),
            'direction': direction,
            'confidence': confidence,
            'obstacles_detected': obstacles,
            'path_clear': not obstacles
        }
        
        return self.handle_communication(nav_update, 'normal')
    
    def send_command_response(self, original_command, status, result_data=None):
        """Send response to Android app command"""
        response = {
            'type': 'command_response',
            'timestamp': time.time(),
            'original_command': original_command,
            'status': status,  # 'success', 'error', 'timeout'
            'result': result_data or {}
        }
        
        return self.handle_communication(response, 'normal')
    
    def process_android_command(self, command_data):
        """Process incoming command from Android app"""
        try:
            command_type = command_data.get('type', 'unknown')
            command_id = command_data.get('command_id', 'unknown')
            timestamp = command_data.get('timestamp', time.time())
            
            # Validate command timing (reject old commands)
            if time.time() - timestamp > 5.0:  # 5 second timeout
                self.send_command_response(command_id, 'timeout', 
                    {'reason': 'Command too old'})
                return False
            
            # Process different command types
            result = None
            if command_type == 'motor_control':
                result = self._handle_motor_command(command_data)
            elif command_type == 'system_config':
                result = self._handle_config_command(command_data)
            elif command_type == 'stream_control':
                result = self._handle_stream_command(command_data)
            elif command_type == 'emergency_stop':
                result = self._handle_emergency_command(command_data)
            else:
                result = {'status': 'error', 'reason': f'Unknown command type: {command_type}'}
            
            # Send response
            status = 'success' if result.get('status') != 'error' else 'error'
            self.send_command_response(command_id, status, result)
            
            return result.get('status') != 'error'
            
        except Exception as e:
            print(f"Error processing Android command: {e}")
            return False
    
    def _handle_motor_command(self, command_data):
        """Handle motor control command from Android app"""
        # This would be implemented by the main system
        return {'status': 'success', 'message': 'Motor command processed'}
    
    def _handle_config_command(self, command_data):
        """Handle configuration command from Android app"""
        return {'status': 'success', 'message': 'Config command processed'}
    
    def _handle_stream_command(self, command_data):
        """Handle video streaming command from Android app"""
        stream_action = command_data.get('action', 'unknown')
        if stream_action == 'start':
            return {'status': 'success', 'message': 'Video stream started'}
        elif stream_action == 'stop':
            return {'status': 'success', 'message': 'Video stream stopped'}
        elif stream_action == 'quality':
            quality = command_data.get('quality', 80)
            return {'status': 'success', 'message': f'Video quality set to {quality}'}
        else:
            return {'status': 'error', 'reason': f'Unknown stream action: {stream_action}'}
    
    def _handle_emergency_command(self, command_data):
        """Handle emergency command from Android app"""
        return {'status': 'success', 'message': 'Emergency command processed'}
    
    def get_protocol_status(self):
        """Get comprehensive protocol status for Android app"""
        protocol_status = self.manage_protocols()
        
        return {
            'protocols': protocol_status,
            'sent_message_count': len(self.sent_messages),
            'primary_protocol': self.primary_protocol,
            'fallback_enabled': self.fallback_enabled,
            'android_app_connected': self._check_android_connection(),
            'connection_quality': self._assess_connection_quality(),
            'data_usage': self._get_data_usage_stats(),
            'last_heartbeat': self._get_last_heartbeat()
        }
    
    def _check_android_connection(self):
        """Check if Android app is actively connected"""
        # Check recent message activity
        if not self.sent_messages:
            return False
        
        # Get most recent message
        recent_messages = sorted(self.sent_messages.values(), 
                               key=lambda x: x['sent_at'], reverse=True)
        
        if recent_messages:
            last_message_time = recent_messages[0]['sent_at']
            # Consider connected if message sent in last 30 seconds
            return (time.time() - time.fromisoformat(last_message_time.replace('Z', '+00:00')).timestamp()) < 30
        
        return False
    
    def _assess_connection_quality(self):
        """Assess connection quality for Android app"""
        wifi_status = self.wifi_handler.get_connection_status()
        ble_status = self.ble_handler.get_connection_status()
        
        if wifi_status['connected'] and ble_status['connected']:
            return 'excellent'
        elif wifi_status['connected']:
            return 'good' if wifi_status['buffered_messages'] < 5 else 'fair'
        elif ble_status['connected']:
            return 'fair' if ble_status['buffered_messages'] < 3 else 'poor'
        else:
            return 'disconnected'
    
    def _get_data_usage_stats(self):
        """Get data usage statistics"""
        total_messages = len(self.sent_messages)
        
        # Estimate data usage (rough calculation)
        estimated_bytes = 0
        for msg_data in self.sent_messages.values():
            msg_str = str(msg_data['message'])
            estimated_bytes += len(msg_str.encode('utf-8'))
        
        return {
            'total_messages': total_messages,
            'estimated_bytes': estimated_bytes,
            'estimated_kb': round(estimated_bytes / 1024, 2)
        }
    
    def _get_last_heartbeat(self):
        """Get timestamp of last heartbeat/keepalive"""
        # This would track heartbeat messages
        return time.time()  # Placeholder
    
    def send_heartbeat(self):
        """Send heartbeat to maintain Android app connection"""
        heartbeat = {
            'type': 'heartbeat',
            'timestamp': time.time(),
            'system_status': 'operational'
        }
        
        return self.handle_communication(heartbeat, 'low')
    
    def start_android_app_service(self):
        """Start services optimized for Android app communication"""
        try:
            # Start heartbeat service
            import threading
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_service)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            
            print("Android app communication services started")
            return True
            
        except Exception as e:
            print(f"Error starting Android app services: {e}")
            return False
    
    def _heartbeat_service(self):
        """Background service to send periodic heartbeats"""
        while True:
            try:
                time.sleep(10)  # Send heartbeat every 10 seconds
                self.send_heartbeat()
            except Exception as e:
                print(f"Heartbeat service error: {e}")
                time.sleep(5)
    
    def cleanup(self):
        """Clean up all protocol resources"""
        print("Cleaning up Android app protocol manager...")
        
        # Send disconnect notification to Android app
        try:
            disconnect_msg = {
                'type': 'system_disconnect',
                'timestamp': time.time(),
                'reason': 'System shutdown'
            }
            self.handle_communication(disconnect_msg, 'high')
            time.sleep(0.5)  # Give time for message to send
        except:
            pass
        
        # Cleanup handlers
        self.wifi_handler.cleanup()
        self.ble_handler.cleanup()
        
        print("Android app protocol manager cleanup complete")