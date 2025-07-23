#!/usr/bin/env python3
"""
Configuration Manager Module
Manages system configuration settings for the smart vehicle
"""

import json
import os
from datetime import datetime

class ConfigManager:
    def __init__(self, config_file='smart_vehicle_config.json'):
        self.config_file = config_file
        self.config_data = {}
        
        # Default configuration optimized for Android app integration
        self.default_config = {
            'vehicle': {
                'name': 'SmartVehicle',
                'id': 'SV001',
                'version': '2.0.0',
                'android_app_version': '1.0.0'
            },
            'vision': {
                'camera_id': 0,
                'resolution': [640, 480],
                'fps_limit': 30,
                'detection_confidence': 0.6,
                'lane_detection': {
                    'lower_white': [0, 0, 180],
                    'upper_white': [180, 40, 255]
                },
                'traffic_light': {
                    'red_hue_ranges': [[0, 10], [170, 180]],
                    'green_hue_range': [35, 85],
                    'min_area': 50,
                    'max_area': 5000
                },
                'speed_limit': {
                    'red_lower': [0, 100, 100],
                    'red_upper': [10, 255, 255],
                    'white_lower': [0, 0, 200],
                    'white_upper': [180, 30, 255]
                },
                'stop_sign': {
                    'red_lower': [0, 70, 50],
                    'red_upper': [10, 255, 255],
                    'min_area': 1000
                }
            },
            'motors': {
                'default_speed': 75,
                'reduced_speed': 50,
                'pins': {
                    'motor1': {'IN1': 17, 'IN2': 22, 'ENA': 18},
                    'motor2': {'IN3': 23, 'IN4': 24, 'ENB': 25},
                    'motor3': {'IN5': 5, 'IN6': 6, 'ENC': 12},
                    'motor4': {'IN7': 13, 'IN8': 19, 'END': 16}
                }
            },
            'sensors': {
                'ultrasonic': {
                    'TRIG': 27,
                    'ECHO': 26,
                    'obstacle_threshold': 20,
                    'safe_distance': 30
                }
            },
            'communication': {
                'wifi': {
                    'server_ip': '192.168.1.100',
                    'server_port': 8080,
                    'reconnect_interval': 5,
                    'buffer_size': 100,
                    'android_optimized': True
                },
                'ble': {
                    'device_name': 'SmartVehicle',
                    'service_uuid': '12345678-1234-1234-1234-123456789abc',
                    'buffer_size': 50,
                    'android_optimized': True
                },
                'protocol': {
                    'primary': 'wifi',
                    'fallback_enabled': True,
                    'heartbeat_interval': 10,
                    'command_timeout': 5
                },
                'android_app': {
                    'video_streaming': {
                        'enabled': True,
                        'default_quality': 80,
                        'max_fps': 15,
                        'resolution': [360, 240]
                    },
                    'telemetry': {
                        'update_rate_hz': 5,
                        'include_video_feed': True,
                        'compression_enabled': True
                    },
                    'ui_preferences': {
                        'theme': 'dark',
                        'show_debug_info': False,
                        'auto_connect': True,
                        'notifications_enabled': True
                    }
                }
            },
            'navigation': {
                'ai': {
                    'decision_history_length': 5,
                    'temporal_filtering_threshold': 0.6,
                    'emergency_stop_distance': 20,
                    'turn_duration': 1.0
                }
            },
            'logging': {
                'level': 'INFO',
                'file_path': 'smart_vehicle.log',
                'max_file_size': 10485760,  # 10MB
                'backup_count': 5
            },
            'performance': {
                'monitoring_enabled': True,
                'cpu_threshold': 80.0,
                'memory_threshold': 80.0,
                'temperature_threshold': 70.0,
                'android_reporting': {
                    'enabled': True,
                    'report_interval': 30,
                    'include_detailed_metrics': False
                }
            },
            'android_integration': {
                'features': {
                    'remote_control': True,
                    'autonomous_mode': True,
                    'emergency_stop': True,
                    'live_streaming': True,
                    'telemetry_monitoring': True,
                    'configuration_management': True
                },
                'security': {
                    'require_authentication': False,
                    'allowed_commands': ['motor_control', 'system_config', 'emergency_stop'],
                    'command_rate_limit': 10  # commands per second
                },
                'data_limits': {
                    'max_video_bitrate_kbps': 500,
                    'max_telemetry_rate_hz': 10,
                    'buffer_size_mb': 5
                }
            }
        }
        
        self.load_config()
        print(f"Configuration Manager initialized - Config file: {config_file}")
        print("Android app integration: ENABLED")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with default config to ensure all fields exist
                self.config_data = self._merge_configs(self.default_config, loaded_config)
                print(f"Configuration loaded from {self.config_file}")
            else:
                print(f"Config file {self.config_file} not found, using default configuration")
                self.config_data = self.default_config.copy()
                self.save_config()  # Create config file with defaults
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration")
            self.config_data = self.default_config.copy()
        
        return self.config_data
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            # Add metadata
            self.config_data['_metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'version': self.config_data['vehicle']['version']
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            
            print(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_config(self, section=None, key=None):
        """Get configuration value(s)"""
        if section is None:
            return self.config_data
        
        if section not in self.config_data:
            print(f"Configuration section '{section}' not found")
            return None
        
        if key is None:
            return self.config_data[section]
        
        if key not in self.config_data[section]:
            print(f"Configuration key '{key}' not found in section '{section}'")
            return None
        
        return self.config_data[section][key]
    
    def set_config(self, section, key, value):
        """Set configuration value"""
        if section not in self.config_data:
            self.config_data[section] = {}
        
        self.config_data[section][key] = value
        print(f"Configuration updated: {section}.{key} = {value}")
        return True
    
    def update_config(self, section, updates):
        """Update multiple configuration values in a section"""
        if section not in self.config_data:
            self.config_data[section] = {}
        
        for key, value in updates.items():
            self.config_data[section][key] = value
        
        print(f"Configuration section '{section}' updated with {len(updates)} changes")
        return True
    
    def reset_to_defaults(self, section=None):
        """Reset configuration to defaults"""
        if section is None:
            self.config_data = self.default_config.copy()
            print("All configuration reset to defaults")
        else:
            if section in self.default_config:
                self.config_data[section] = self.default_config[section].copy()
                print(f"Configuration section '{section}' reset to defaults")
            else:
                print(f"Default configuration for section '{section}' not found")
                return False
        
        return True
    
    def _merge_configs(self, default, loaded):
        """Recursively merge loaded config with default config"""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def validate_config(self):
        """Validate configuration values"""
        validation_errors = []
        
        # Validate vision settings
        vision_config = self.get_config('vision')
        if vision_config:
            if not isinstance(vision_config.get('resolution'), list) or len(vision_config['resolution']) != 2:
                validation_errors.append("Vision resolution must be a list of 2 integers")
            
            if vision_config.get('fps_limit', 0) <= 0:
                validation_errors.append("Vision FPS limit must be positive")
        
        # Validate motor settings
        motors_config = self.get_config('motors')
        if motors_config:
            for speed_key in ['default_speed', 'reduced_speed']:
                speed = motors_config.get(speed_key, 0)
                if not 0 <= speed <= 100:
                    validation_errors.append(f"Motor {speed_key} must be between 0 and 100")
        
        # Validate sensor settings
        sensors_config = self.get_config('sensors', 'ultrasonic')
        if sensors_config:
            threshold = sensors_config.get('obstacle_threshold', 0)
            if threshold <= 0:
                validation_errors.append("Ultrasonic obstacle threshold must be positive")
        
        if validation_errors:
            print("Configuration validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
            return False
        
        print("Configuration validation passed")
        return True
    
    def export_config(self, export_file):
        """Export configuration to a different file"""
        try:
            with open(export_file, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            print(f"Configuration exported to {export_file}")
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False
    
    def get_config_summary(self):
        """Get a comprehensive configuration summary for Android app"""
        summary = {
            'vehicle_info': {
                'name': self.get_config('vehicle', 'name'),
                'id': self.get_config('vehicle', 'id'),
                'version': self.get_config('vehicle', 'version'),
                'android_app_version': self.get_config('vehicle', 'android_app_version')
            },
            'system_config': {
                'vision_resolution': self.get_config('vision', 'resolution'),
                'primary_protocol': self.get_config('communication', 'protocol')['primary'],
                'motor_default_speed': self.get_config('motors', 'default_speed'),
                'sensor_threshold': self.get_config('sensors', 'ultrasonic')['obstacle_threshold']
            },
            'android_features': {
                'video_streaming_enabled': self.get_config('android_integration', 'features')['live_streaming'],
                'remote_control_enabled': self.get_config('android_integration', 'features')['remote_control'],
                'autonomous_mode_enabled': self.get_config('android_integration', 'features')['autonomous_mode'],
                'video_quality': self.get_config('communication', 'android_app')['video_streaming']['default_quality'],
                'telemetry_rate': self.get_config('communication', 'android_app')['telemetry']['update_rate_hz']
            },
            'metadata': {
                'config_file': self.config_file,
                'last_updated': self.config_data.get('_metadata', {}).get('last_updated', 'Unknown'),
                'android_integration_enabled': True
            }
        }
        return summary
    
    def get_android_app_config(self):
        """Get configuration specifically for Android app"""
        return {
            'communication': self.get_config('communication', 'android_app'),
            'features': self.get_config('android_integration', 'features'),
            'security': self.get_config('android_integration', 'security'),
            'data_limits': self.get_config('android_integration', 'data_limits'),
            'vehicle_info': {
                'name': self.get_config('vehicle', 'name'),
                'id': self.get_config('vehicle', 'id')
            }
        }
    
    def update_android_app_config(self, updates):
        """Update Android app specific configuration"""
        try:
            current_android_config = self.get_config('communication', 'android_app')
            if current_android_config:
                # Merge updates with current config
                for key, value in updates.items():
                    if key in current_android_config:
                        if isinstance(current_android_config[key], dict) and isinstance(value, dict):
                            current_android_config[key].update(value)
                        else:
                            current_android_config[key] = value
                
                self.set_config('communication', 'android_app', current_android_config)
                return True
            return False
        except Exception as e:
            print(f"Error updating Android app config: {e}")
            return False
    
    def validate_android_config(self):
        """Validate Android-specific configuration"""
        validation_errors = []
        
        # Validate Android app configuration
        android_config = self.get_config('communication', 'android_app')
        if android_config:
            # Video streaming validation
            video_config = android_config.get('video_streaming', {})
            quality = video_config.get('default_quality', 80)
            if not 10 <= quality <= 100:
                validation_errors.append("Video quality must be between 10 and 100")
            
            max_fps = video_config.get('max_fps', 15)
            if not 1 <= max_fps <= 30:
                validation_errors.append("Max FPS must be between 1 and 30")
            
            # Telemetry validation
            telemetry_config = android_config.get('telemetry', {})
            update_rate = telemetry_config.get('update_rate_hz', 5)
            if not 1 <= update_rate <= 20:
                validation_errors.append("Telemetry update rate must be between 1 and 20 Hz")
        
        # Validate Android integration settings
        integration_config = self.get_config('android_integration')
        if integration_config:
            # Data limits validation
            data_limits = integration_config.get('data_limits', {})
            bitrate = data_limits.get('max_video_bitrate_kbps', 500)
            if not 100 <= bitrate <= 2000:
                validation_errors.append("Video bitrate must be between 100 and 2000 kbps")
            
            # Security validation
            security_config = integration_config.get('security', {})
            rate_limit = security_config.get('command_rate_limit', 10)
            if not 1 <= rate_limit <= 50:
                validation_errors.append("Command rate limit must be between 1 and 50 per second")
        
        if validation_errors:
            print("Android configuration validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
            return False
        
        print("Android configuration validation passed")
        return True