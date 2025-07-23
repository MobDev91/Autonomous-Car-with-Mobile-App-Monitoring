#!/usr/bin/env python3
"""
Logger Module
Comprehensive logging system for the smart vehicle
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime

class Logger:
    def __init__(self, name='SmartVehicle', config=None):
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Default configuration
        self.default_config = {
            'level': 'INFO',
            'file_path': 'smart_vehicle.log',
            'max_file_size': 10485760,  # 10MB
            'backup_count': 5,
            'console_output': True,
            'json_format': False
        }
        
        # Use provided config or defaults
        if config:
            self.config = {**self.default_config, **config}
        else:
            self.config = self.default_config
        
        self.setup_logging()
        self.log_info("Logger initialized")
    
    def setup_logging(self):
        """Set up logging configuration"""
        # Clear existing handlers
        self.logger.handlers = []
        
        # Set logging level
        level = getattr(logging, self.config['level'].upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Create formatters
        if self.config.get('json_format', False):
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # File handler with rotation
        if self.config['file_path']:
            try:
                # Ensure directory exists
                log_dir = os.path.dirname(self.config['file_path'])
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                file_handler = logging.handlers.RotatingFileHandler(
                    self.config['file_path'],
                    maxBytes=self.config['max_file_size'],
                    backupCount=self.config['backup_count']
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
                
            except Exception as e:
                print(f"Error setting up file logging: {e}")
        
        # Console handler
        if self.config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def log_debug(self, message, extra_data=None):
        """Log debug message"""
        self._log_with_extra(logging.DEBUG, message, extra_data)
    
    def log_info(self, message, extra_data=None):
        """Log info message"""
        self._log_with_extra(logging.INFO, message, extra_data)
    
    def log_warning(self, message, extra_data=None):
        """Log warning message"""
        self._log_with_extra(logging.WARNING, message, extra_data)
    
    def log_error(self, message, extra_data=None):
        """Log error message"""
        self._log_with_extra(logging.ERROR, message, extra_data)
    
    def log_critical(self, message, extra_data=None):
        """Log critical message"""
        self._log_with_extra(logging.CRITICAL, message, extra_data)
    
    def _log_with_extra(self, level, message, extra_data):
        """Log message with optional extra data"""
        if extra_data:
            if self.config.get('json_format', False):
                # Extra data will be included in JSON format
                self.logger.log(level, message, extra={'extra_data': extra_data})
            else:
                # Append extra data to message
                extra_str = json.dumps(extra_data, default=str)
                self.logger.log(level, f"{message} | Extra: {extra_str}")
        else:
            self.logger.log(level, message)
    
    def log_vision_event(self, event_type, details):
        """Log vision system events"""
        self.log_info(f"Vision Event: {event_type}", {
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_navigation_decision(self, decision, environment):
        """Log navigation decisions"""
        self.log_info(f"Navigation Decision: {decision['action']}", {
            'decision': decision,
            'environment': environment,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_motor_action(self, action, parameters):
        """Log motor control actions"""
        self.log_info(f"Motor Action: {action}", {
            'action': action,
            'parameters': parameters,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_sensor_data(self, sensor_type, data):
        """Log sensor readings"""
        self.log_debug(f"Sensor Data: {sensor_type}", {
            'sensor_type': sensor_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_communication_event(self, protocol, event_type, details):
        """Log communication events"""
        self.log_info(f"Communication [{protocol}]: {event_type}", {
            'protocol': protocol,
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_performance_metrics(self, metrics):
        """Log performance metrics"""
        self.log_debug("Performance Metrics", {
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_system_status(self, status):
        """Log system status"""
        self.log_info("System Status Update", {
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_android_command(self, command_type, command_data, result=None):
        """Log Android app commands with detailed context"""
        self.log_info(f"Android Command: {command_type}", {
            'command_type': command_type,
            'command_data': command_data,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'source': 'android_app'
        })
    
    def log_video_stream_event(self, event_type, frame_info=None):
        """Log video streaming events for Android app"""
        self.log_debug(f"Video Stream: {event_type}", {
            'event_type': event_type,
            'frame_info': frame_info,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_telemetry_data(self, telemetry_type, data_size, transmission_time=None):
        """Log telemetry data transmission to Android app"""
        self.log_debug(f"Telemetry Sent: {telemetry_type}", {
            'telemetry_type': telemetry_type,
            'data_size_bytes': data_size,
            'transmission_time_ms': transmission_time,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_android_connection_event(self, event_type, connection_info):
        """Log Android app connection events"""
        level = logging.INFO if event_type in ['connected', 'disconnected'] else logging.DEBUG
        self._log_with_extra(level, f"Android Connection: {event_type}", {
            'event_type': event_type,
            'connection_info': connection_info,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_protocol_switch(self, from_protocol, to_protocol, reason):
        """Log protocol switching for Android app communication"""
        self.log_warning(f"Protocol Switch: {from_protocol} -> {to_protocol}", {
            'from_protocol': from_protocol,
            'to_protocol': to_protocol,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_emergency_event(self, event_type, trigger_source, sensor_data=None):
        """Log emergency events with critical priority"""
        self.log_critical(f"Emergency Event: {event_type}", {
            'event_type': event_type,
            'trigger_source': trigger_source,
            'sensor_data': sensor_data,
            'timestamp': datetime.now().isoformat(),
            'requires_immediate_attention': True
        })
    
    def log_exception(self, exception, context=None):
        """Log exception with context"""
        error_data = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'timestamp': datetime.now().isoformat()
        }
        
        if context:
            error_data['context'] = context
        
        self.log_error(f"Exception occurred: {type(exception).__name__}", error_data)
    
    def set_level(self, level):
        """Change logging level"""
        level_obj = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(level_obj)
        self.config['level'] = level.upper()
        self.log_info(f"Logging level changed to {level.upper()}")
    
    def get_log_stats(self):
        """Get comprehensive logging statistics for Android app"""
        stats = {
            'logger_name': self.name,
            'current_level': self.config['level'],
            'handlers_count': len(self.logger.handlers),
            'log_file': self.config['file_path'],
            'json_format': self.config.get('json_format', False),
            'android_integration': True
        }
        
        # Get log file size and details if it exists
        if self.config['file_path'] and os.path.exists(self.config['file_path']):
            try:
                file_size = os.path.getsize(self.config['file_path'])
                stats['log_file_size_bytes'] = file_size
                stats['log_file_size_mb'] = round(file_size / (1024 * 1024), 2)
                
                # Get file modification time
                mod_time = os.path.getmtime(self.config['file_path'])
                stats['last_modified'] = datetime.fromtimestamp(mod_time).isoformat()
            except Exception as e:
                stats['log_file_error'] = str(e)
        
        return stats
    
    def get_recent_logs(self, count=50, level_filter=None):
        """Get recent log entries for Android app display"""
        try:
            if not self.config['file_path'] or not os.path.exists(self.config['file_path']):
                return []
            
            recent_logs = []
            with open(self.config['file_path'], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get last 'count' lines
            recent_lines = lines[-count:] if len(lines) > count else lines
            
            for line in recent_lines:
                line = line.strip()
                if line:
                    # Parse log entry (basic parsing)
                    if level_filter:
                        if level_filter.upper() not in line:
                            continue
                    
                    recent_logs.append({
                        'raw_line': line,
                        'timestamp': self._extract_timestamp(line),
                        'level': self._extract_level(line)
                    })
            
            return recent_logs
            
        except Exception as e:
            self.log_exception(e, "Error retrieving recent logs")
            return []
    
    def _extract_timestamp(self, log_line):
        """Extract timestamp from log line"""
        try:
            # Basic timestamp extraction (adapt based on format)
            parts = log_line.split(' - ')
            if len(parts) > 0:
                return parts[0]
        except:
            pass
        return 'Unknown'
    
    def _extract_level(self, log_line):
        """Extract log level from log line"""
        for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
            if level in log_line:
                return level
        return 'UNKNOWN'
    
    def export_logs_for_android(self, export_path=None, include_system_info=True):
        """Export logs in Android-friendly format"""
        try:
            if export_path is None:
                export_path = f"android_logs_export_{int(time.time())}.json"
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'logger_stats': self.get_log_stats(),
                'recent_logs': self.get_recent_logs(100)
            }
            
            if include_system_info:
                import platform
                export_data['system_info'] = {
                    'platform': platform.system(),
                    'python_version': platform.python_version(),
                    'hostname': platform.node()
                }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.log_info(f"Logs exported for Android app: {export_path}")
            return export_path
            
        except Exception as e:
            self.log_exception(e, "Error exporting logs for Android")
            return None
    
    def cleanup(self):
        """Clean up logger resources"""
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers = []
        self.log_info("Logger cleanup completed")

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'logger': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra data if present
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)