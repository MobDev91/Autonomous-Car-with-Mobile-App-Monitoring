#!/usr/bin/env python3
"""
WiFi Handler Module
Manages WiFi communications for the smart vehicle
"""

import socket
import json
import time
import threading
from datetime import datetime

class WiFiHandler:
    def __init__(self, server_ip='192.168.1.100', server_port=8080):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None
        self.connected = False
        self.connection_thread = None
        self.reconnect_interval = 5  # seconds
        
        # Data buffer for sending
        self.data_buffer = []
        self.max_buffer_size = 100
        
        print(f"WiFi Handler initialized - Target: {server_ip}:{server_port}")
    
    def connect_wifi(self):
        """Establish WiFi connection to server"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)  # 10 second timeout
            self.client_socket.connect((self.server_ip, self.server_port))
            self.connected = True
            print(f"Connected to WiFi server {self.server_ip}:{self.server_port}")
            return True
        except Exception as e:
            print(f"WiFi connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect_wifi(self):
        """Disconnect from WiFi server"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.connected = False
        print("WiFi disconnected")
    
    def send_data(self, data):
        """Send data over WiFi connection"""
        if not self.connected:
            print("WiFi not connected - buffering data")
            self._buffer_data(data)
            return False
        
        try:
            # Prepare data packet
            packet = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Convert to JSON and send
            json_data = json.dumps(packet) + '\n'
            self.client_socket.send(json_data.encode('utf-8'))
            return True
            
        except Exception as e:
            print(f"WiFi send error: {e}")
            self.connected = False
            self._buffer_data(data)
            return False
    
    def receive_data(self):
        """Receive data from WiFi connection"""
        if not self.connected:
            return None
        
        try:
            self.client_socket.settimeout(1)  # 1 second timeout for non-blocking
            data = self.client_socket.recv(1024)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except socket.timeout:
            return None
        except Exception as e:
            print(f"WiFi receive error: {e}")
            self.connected = False
            return None
    
    def _buffer_data(self, data):
        """Buffer data when connection is not available"""
        if len(self.data_buffer) >= self.max_buffer_size:
            self.data_buffer.pop(0)  # Remove oldest data
        
        self.data_buffer.append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
    
    def _send_buffered_data(self):
        """Send all buffered data when connection is restored"""
        if not self.connected or not self.data_buffer:
            return
        
        print(f"Sending {len(self.data_buffer)} buffered messages")
        failed_sends = []
        
        for buffered_item in self.data_buffer:
            if not self.send_data(buffered_item['data']):
                failed_sends.append(buffered_item)
        
        # Keep failed sends in buffer
        self.data_buffer = failed_sends
    
    def start_auto_reconnect(self):
        """Start automatic reconnection thread"""
        if self.connection_thread and self.connection_thread.is_alive():
            return
        
        self.connection_thread = threading.Thread(target=self._auto_reconnect_loop)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        print("Auto-reconnect thread started")
    
    def _auto_reconnect_loop(self):
        """Auto-reconnection loop"""
        while True:
            if not self.connected:
                print("Attempting WiFi reconnection...")
                if self.connect_wifi():
                    self._send_buffered_data()
            
            time.sleep(self.reconnect_interval)
    
    def send_telemetry(self, vision_data, sensor_data, navigation_data):
        """Send comprehensive telemetry data"""
        telemetry = {
            'type': 'telemetry',
            'vision': vision_data,
            'sensors': sensor_data,
            'navigation': navigation_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.send_data(telemetry)
    
    def send_status(self, status_message):
        """Send status message"""
        status = {
            'type': 'status',
            'message': status_message,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.send_data(status)
    
    def get_connection_status(self):
        """Get current connection status"""
        return {
            'connected': self.connected,
            'server_ip': self.server_ip,
            'server_port': self.server_port,
            'buffered_messages': len(self.data_buffer)
        }
    
    def cleanup(self):
        """Clean up WiFi resources"""
        self.disconnect_wifi()
        if self.connection_thread and self.connection_thread.is_alive():
            # Note: Thread will terminate when main program ends
            pass