#!/usr/bin/env python3
"""
Navigation AI Module
Intelligent navigation system that combines vision and sensor data for autonomous driving
"""

import time
from collections import deque

class NavigationAI:
    def __init__(self):
        # Navigation state
        self.current_state = "IDLE"
        self.previous_actions = deque(maxlen=10)
        
        # Decision history for temporal filtering
        self.decision_history = deque(maxlen=5)
        
        # Navigation parameters
        self.obstacle_stop_distance = 20  # cm
        self.safe_distance = 30  # cm
        self.turn_duration = 1.0  # seconds
        
        # Traffic light behavior
        self.red_light_stop = True
        self.green_light_go = True
        
        # Speed limits
        self.default_speed = 75
        self.reduced_speed = 50
        
        print("Navigation AI initialized")
    
    def analyze_environment(self, vision_data, sensor_data):
        """Analyze environment data and extract relevant information"""
        environment = {
            'lane_direction': vision_data.get('lane_direction', 'UNKNOWN'),
            'traffic_light': vision_data.get('traffic_light_status', 'UNKNOWN'),
            'traffic_light_confidence': vision_data.get('traffic_light_confidence', 0),
            'speed_limit_detected': vision_data.get('speed_limit_detected', False),
            'stop_sign_detected': vision_data.get('stop_sign_detected', False),
            'obstacle_distance': sensor_data.get('distance', 400),
            'obstacle_detected': sensor_data.get('obstacle_detected', False)
        }
        return environment
    
    def make_navigation_decision(self, environment):
        """Make navigation decision based on environment analysis"""
        # Priority-based decision making
        
        # 1. Emergency stop for obstacles
        if environment['obstacle_detected'] and environment['obstacle_distance'] < self.obstacle_stop_distance:
            return {
                'action': 'EMERGENCY_STOP',
                'speed': 0,
                'reason': f"Obstacle at {environment['obstacle_distance']}cm"
            }
        
        # 2. Stop for red traffic light
        if (environment['traffic_light'] == 'RED' and 
            environment['traffic_light_confidence'] > 0.7):
            return {
                'action': 'TRAFFIC_STOP',
                'speed': 0,
                'reason': 'Red traffic light detected'
            }
        
        # 3. Stop for stop sign
        if environment['stop_sign_detected']:
            return {
                'action': 'STOP_SIGN_STOP',
                'speed': 0,
                'reason': 'Stop sign detected'
            }
        
        # 4. Determine movement based on lane direction
        if environment['lane_direction'] == 'LEFT':
            speed = self.reduced_speed if environment['speed_limit_detected'] else self.default_speed
            return {
                'action': 'TURN_LEFT',
                'speed': speed,
                'reason': 'Following lane direction'
            }
        elif environment['lane_direction'] == 'RIGHT':
            speed = self.reduced_speed if environment['speed_limit_detected'] else self.default_speed
            return {
                'action': 'TURN_RIGHT',
                'speed': speed,
                'reason': 'Following lane direction'
            }
        elif environment['lane_direction'] == 'STRAIGHT':
            # Reduce speed if obstacle is close but not immediate danger
            if environment['obstacle_distance'] < self.safe_distance:
                speed = self.reduced_speed
            else:
                speed = self.reduced_speed if environment['speed_limit_detected'] else self.default_speed
            return {
                'action': 'MOVE_FORWARD',
                'speed': speed,
                'reason': 'Following lane - straight path'
            }
        
        # 5. Default behavior when lane direction is unknown
        if environment['obstacle_distance'] > self.safe_distance:
            return {
                'action': 'MOVE_FORWARD',
                'speed': self.reduced_speed,
                'reason': 'Cautious forward movement'
            }
        else:
            return {
                'action': 'STOP',
                'speed': 0,
                'reason': 'Uncertain environment - safety stop'
            }
    
    def apply_temporal_filtering(self, decision):
        """Apply temporal filtering to avoid rapid decision changes"""
        self.decision_history.append(decision['action'])
        
        # Count occurrences of each action
        action_counts = {}
        for action in self.decision_history:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Find most common action
        most_common_action = max(action_counts, key=action_counts.get)
        most_common_count = action_counts[most_common_action]
        
        # Apply filtering - require at least 60% consensus
        if most_common_count >= len(self.decision_history) * 0.6:
            decision['action'] = most_common_action
            decision['filtered'] = True
        else:
            decision['filtered'] = False
        
        return decision
    
    def process_navigation(self, vision_data, sensor_data):
        """Main navigation processing function"""
        # Analyze environment
        environment = self.analyze_environment(vision_data, sensor_data)
        
        # Make decision
        decision = self.make_navigation_decision(environment)
        
        # Apply temporal filtering
        filtered_decision = self.apply_temporal_filtering(decision)
        
        # Update state
        self.current_state = filtered_decision['action']
        self.previous_actions.append(filtered_decision['action'])
        
        return filtered_decision
    
    def make_decision(self, vision_data=None, sensor_data=None):
        """Simplified decision making interface"""
        if vision_data is None:
            vision_data = {}
        if sensor_data is None:
            sensor_data = {}
            
        return self.process_navigation(vision_data, sensor_data)
    
    def get_navigation_status(self):
        """Get current navigation status"""
        return {
            'current_state': self.current_state,
            'recent_actions': list(self.previous_actions),
            'decision_history': list(self.decision_history)
        }