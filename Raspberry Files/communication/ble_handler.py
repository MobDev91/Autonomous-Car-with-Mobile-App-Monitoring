#!/usr/bin/env python3
"""
Bluetooth Low Energy Handler Module
Manages BLE communications for the smart vehicle
"""

import time
import json
import threading
from datetime import datetime

try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    print("Warning: Bluetooth library not available. BLE functionality will be limited.")

class BLEHandler:
    def __init__(self, device_name="SmartVehicle", service_uuid="12345678-1234-1234-1234-123456789abc"):
        self.device_name = device_name
        self.service_uuid = service_uuid
        self.server_socket = None
        self.client_socket = None
        self.client_info = None
        self.connected = False
        self.advertising = False
        
        # Data buffer for sending
        self.data_buffer = []
        self.max_buffer_size = 50
        
        # Threading
        self.server_thread = None
        self.running = False
        
        print(f"BLE Handler initialized - Device: {device_name}")
        if not BLUETOOTH_AVAILABLE:
            print("BLE functionality will be simulated")
    
    def start_advertising(self):
        """Start BLE advertising to allow connections"""
        if not BLUETOOTH_AVAILABLE:
            print("BLE advertising simulated (Bluetooth not available)")
            self.advertising = True
            return True
        
        try:
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", bluetooth.PORT_ANY))
            self.server_socket.listen(1)
            
            port = self.server_socket.getsockname()[1]
            
            # Advertise service
            bluetooth.advertise_service(
                self.server_socket, 
                self.device_name,
                service_id=self.service_uuid,
                service_classes=[bluetooth.SERIAL_PORT_CLASS],
                profiles=[bluetooth.SERIAL_PORT_PROFILE]
            )
            
            self.advertising = True
            self.running = True
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._accept_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"BLE advertising started on RFCOMM channel {port}")
            return True
            
        except Exception as e:
            print(f"BLE advertising failed: {e}")
            return False
    
    def stop_advertising(self):
        """Stop BLE advertising"""
        self.advertising = False
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("BLE advertising stopped")
    
    def _accept_connections(self):
        """Accept incoming BLE connections"""
        while self.running:
            try:
                print("Waiting for BLE connection...")
                self.client_socket, self.client_info = self.server_socket.accept()
                self.connected = True
                print(f"BLE client connected: {self.client_info}")
                
                # Send buffered data
                self._send_buffered_data()
                
                # Keep connection alive
                while self.connected and self.running:
                    time.sleep(1)
                    
            except Exception as e:
                if self.running:
                    print(f"BLE connection error: {e}")
                self.connected = False
                time.sleep(1)
    
    def connect_ble(self, target_address=None):
        """Connect to a BLE device (client mode)"""
        if not BLUETOOTH_AVAILABLE:
            print("BLE connection simulated")
            self.connected = True
            return True
        
        if not target_address:
            print("No target address provided for BLE connection")
            return False
        
        try:
            self.client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.client_socket.connect((target_address, 1))  # RFCOMM channel 1
            self.connected = True
            print(f"Connected to BLE device: {target_address}")
            return True
            
        except Exception as e:
            print(f"BLE connection failed: {e}")
            return False
    
    def disconnect_ble(self):
        """Disconnect BLE connection"""
        self.connected = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        print("BLE disconnected")
    
    def transmit_data(self, data):
        """Transmit data over BLE connection"""
        if not self.connected:
            print("BLE not connected - buffering data")
            self._buffer_data(data)
            return False
        
        if not BLUETOOTH_AVAILABLE:
            print(f"BLE data transmitted (simulated): {data}")
            return True
        
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
            print(f"BLE transmit error: {e}")
            self.connected = False
            self._buffer_data(data)
            return False
    
    def receive_data(self):
        """Receive data from BLE connection"""
        if not self.connected or not BLUETOOTH_AVAILABLE:
            return None
        
        try:
            self.client_socket.settimeout(1)  # 1 second timeout
            data = self.client_socket.recv(1024)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
            
        except bluetooth.btcommon.BluetoothError:
            return None
        except Exception as e:
            print(f"BLE receive error: {e}")
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
        
        print(f"Sending {len(self.data_buffer)} buffered BLE messages")
        failed_sends = []
        
        for buffered_item in self.data_buffer:
            if not self.transmit_data(buffered_item['data']):
                failed_sends.append(buffered_item)
        
        # Keep failed sends in buffer
        self.data_buffer = failed_sends
    
    def send_vehicle_status(self, status_data):
        """Send vehicle status via BLE"""
        status = {
            'type': 'vehicle_status',
            'status': status_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.transmit_data(status)
    
    def send_alert(self, alert_message, severity='info'):
        """Send alert message via BLE"""
        alert = {
            'type': 'alert',
            'message': alert_message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.transmit_data(alert)
    
    def get_connection_status(self):
        """Get current BLE connection status"""
        return {
            'connected': self.connected,
            'advertising': self.advertising,
            'device_name': self.device_name,
            'client_info': self.client_info,
            'buffered_messages': len(self.data_buffer),
            'bluetooth_available': BLUETOOTH_AVAILABLE
        }
    
    def cleanup(self):
        """Clean up BLE resources"""
        self.stop_advertising()
        self.disconnect_ble()