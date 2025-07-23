#!/usr/bin/env python3
"""
Performance Monitor Module
Monitors system performance and resource usage for the smart vehicle
"""

import time
import threading
from datetime import datetime
from collections import deque

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Performance monitoring will be limited.")

class PerformanceMonitor:
    def __init__(self, config=None):
        # Default configuration
        self.default_config = {
            'monitoring_enabled': True,
            'cpu_threshold': 80.0,
            'memory_threshold': 80.0,
            'temperature_threshold': 70.0,
            'monitoring_interval': 5.0,  # seconds
            'history_length': 60  # Keep 60 measurements (5 minutes at 5s intervals)
        }
        
        # Use provided config or defaults
        if config:
            self.config = {**self.default_config, **config}
        else:
            self.config = self.default_config
        
        # Performance data storage
        self.cpu_history = deque(maxlen=self.config['history_length'])
        self.memory_history = deque(maxlen=self.config['history_length'])
        self.temperature_history = deque(maxlen=self.config['history_length'])
        self.fps_history = deque(maxlen=self.config['history_length'])
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.alert_callbacks = []
        
        # Performance counters
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        print(f"Performance Monitor initialized (psutil available: {PSUTIL_AVAILABLE})")
    
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        if not self.config['monitoring_enabled']:
            print("Performance monitoring is disabled")
            return False
        
        if self.monitoring_active:
            print("Performance monitoring already active")
            return True
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        print("Performance monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop continuous performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
        
        print("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect performance metrics
                metrics = self.collect_metrics()
                
                # Store in history
                self._store_metrics(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Sleep until next monitoring cycle
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(self.config['monitoring_interval'])
    
    def collect_metrics(self):
        """Collect current performance metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': self.monitor_cpu(),
            'memory_percent': self.monitor_memory(),
            'temperature': self.monitor_temperature(),
            'fps': self.current_fps
        }
        
        if PSUTIL_AVAILABLE:
            # Additional metrics if psutil is available
            try:
                metrics.update({
                    'disk_usage': psutil.disk_usage('/').percent,
                    'network_io': self._get_network_io(),
                    'process_count': len(psutil.pids())
                })
            except:
                pass
        
        return metrics
    
    def monitor_cpu(self):
        """Monitor CPU usage percentage"""
        if not PSUTIL_AVAILABLE:
            # Simulate CPU monitoring
            return 25.0  # Placeholder value
        
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            print(f"Error monitoring CPU: {e}")
            return 0.0
    
    def monitor_memory(self):
        """Monitor memory usage percentage"""
        if not PSUTIL_AVAILABLE:
            # Simulate memory monitoring
            return 45.0  # Placeholder value
        
        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            print(f"Error monitoring memory: {e}")
            return 0.0
    
    def monitor_temperature(self):
        """Monitor system temperature"""
        if not PSUTIL_AVAILABLE:
            # Simulate temperature monitoring
            return 45.0  # Placeholder value
        
        try:
            # Try to get CPU temperature (Raspberry Pi specific)
            temperatures = psutil.sensors_temperatures()
            
            if 'cpu_thermal' in temperatures:
                return temperatures['cpu_thermal'][0].current
            elif 'coretemp' in temperatures:
                return temperatures['coretemp'][0].current
            else:
                # Fallback - estimate based on CPU usage
                cpu_percent = psutil.cpu_percent()
                return 30 + (cpu_percent * 0.4)  # Rough estimation
                
        except Exception as e:
            print(f"Error monitoring temperature: {e}")
            return 0.0
    
    def _get_network_io(self):
        """Get network I/O statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except:
            return None
    
    def update_fps(self, frame_processed=True):
        """Update FPS counter"""
        if frame_processed:
            self.frame_count += 1
        
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 1.0:  # Update FPS every second
            self.current_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def _store_metrics(self, metrics):
        """Store metrics in history"""
        self.cpu_history.append({
            'timestamp': metrics['timestamp'],
            'value': metrics['cpu_percent']
        })
        
        self.memory_history.append({
            'timestamp': metrics['timestamp'],
            'value': metrics['memory_percent']
        })
        
        self.temperature_history.append({
            'timestamp': metrics['timestamp'],
            'value': metrics['temperature']
        })
        
        self.fps_history.append({
            'timestamp': metrics['timestamp'],
            'value': metrics['fps']
        })
    
    def _check_alerts(self, metrics):
        """Check for performance alerts"""
        alerts = []
        
        # CPU alert
        if metrics['cpu_percent'] > self.config['cpu_threshold']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                'value': metrics['cpu_percent'],
                'threshold': self.config['cpu_threshold']
            })
        
        # Memory alert
        if metrics['memory_percent'] > self.config['memory_threshold']:
            alerts.append({
                'type': 'memory_high',
                'message': f"High memory usage: {metrics['memory_percent']:.1f}%",
                'value': metrics['memory_percent'],
                'threshold': self.config['memory_threshold']
            })
        
        # Temperature alert
        if metrics['temperature'] > self.config['temperature_threshold']:
            alerts.append({
                'type': 'temperature_high',
                'message': f"High temperature: {metrics['temperature']:.1f}°C",
                'value': metrics['temperature'],
                'threshold': self.config['temperature_threshold']
            })
        
        # Low FPS alert
        if metrics['fps'] < 10 and metrics['fps'] > 0:
            alerts.append({
                'type': 'fps_low',
                'message': f"Low FPS: {metrics['fps']:.1f}",
                'value': metrics['fps'],
                'threshold': 10
            })
        
        # Trigger alert callbacks
        for alert in alerts:
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert):
        """Trigger performance alert"""
        print(f"Performance Alert: {alert['message']}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback):
        """Add callback function for performance alerts"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self):
        """Get current performance metrics"""
        return self.collect_metrics()
    
    def get_performance_summary(self):
        """Get performance summary with averages"""
        summary = {
            'current': self.collect_metrics(),
            'averages': {},
            'monitoring_active': self.monitoring_active,
            'config': self.config
        }
        
        # Calculate averages if we have history
        if self.cpu_history:
            summary['averages']['cpu'] = sum(item['value'] for item in self.cpu_history) / len(self.cpu_history)
        
        if self.memory_history:
            summary['averages']['memory'] = sum(item['value'] for item in self.memory_history) / len(self.memory_history)
        
        if self.temperature_history:
            summary['averages']['temperature'] = sum(item['value'] for item in self.temperature_history) / len(self.temperature_history)
        
        if self.fps_history:
            fps_values = [item['value'] for item in self.fps_history if item['value'] > 0]
            if fps_values:
                summary['averages']['fps'] = sum(fps_values) / len(fps_values)
        
        return summary
    
    def get_history(self, metric_type='all'):
        """Get performance history"""
        history = {}
        
        if metric_type in ['all', 'cpu']:
            history['cpu'] = list(self.cpu_history)
        
        if metric_type in ['all', 'memory']:
            history['memory'] = list(self.memory_history)
        
        if metric_type in ['all', 'temperature']:
            history['temperature'] = list(self.temperature_history)
        
        if metric_type in ['all', 'fps']:
            history['fps'] = list(self.fps_history)
        
        return history
    
    def reset_history(self):
        """Reset performance history"""
        self.cpu_history.clear()
        self.memory_history.clear()
        self.temperature_history.clear()
        self.fps_history.clear()
        print("Performance history reset")
    
    def cleanup(self):
        """Clean up performance monitor resources"""
        self.stop_monitoring()
        self.alert_callbacks.clear()
        print("Performance monitor cleanup completed")