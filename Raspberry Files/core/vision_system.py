#!/usr/bin/env python3
"""
Smart Navigation Vision System
Advanced computer vision for autonomous navigation with lane detection,
obstacle recognition, and real-time Android app streaming capabilities.
"""

import cv2
import numpy as np
import time
import os
from collections import deque

class NavigationVisionSystem:
    def __init__(self, camera_id=0, resolution=(640, 480), android_streaming=True):
        """Initialize the navigation vision system"""
        self.camera = cv2.VideoCapture(camera_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.resolution = resolution
        
        # Performance tracking
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Android app integration
        self.android_streaming = android_streaming
        self.stream_frame = None
        self.stream_quality = 80  # JPEG quality for streaming
        
        # Lane detection parameters (optimized for navigation)
        self.lane_lower_white = np.array([0, 0, 180])
        self.lane_upper_white = np.array([180, 40, 255])
        self.lane_lower_yellow = np.array([15, 80, 100])  # Yellow lane markers
        self.lane_upper_yellow = np.array([35, 255, 255])
        
        # Obstacle detection parameters
        self.obstacle_lower_bound = np.array([0, 0, 0])
        self.obstacle_upper_bound = np.array([180, 255, 100])
        self.min_obstacle_area = 2000
        
        # Path detection parameters
        self.path_roi_y_start = int(resolution[1] * 0.6)  # Bottom 40% of image
        self.path_roi_y_end = resolution[1]
        
        # Detection history for temporal filtering
        self.history_length = 5
        self.lane_direction_history = []
        self.current_direction = "STRAIGHT"
        self.lane_confidence = 0
        
        # Obstacle detection history
        self.obstacle_history = []
        self.obstacle_detected = False
        self.obstacle_confidence = 0
        
        # Navigation data for Android app
        self.navigation_data = {
            'lane_direction': 'STRAIGHT',
            'lane_confidence': 0,
            'obstacle_detected': False,
            'obstacle_distance_pixels': 0,
            'path_clear': True,
            'fps': 0,
            'camera_active': True
        }
        
        # Frame processing settings
        self.skip_frames = 2  # Process every 2nd frame for performance
        self.frame_skip_counter = 0
        
        print("Navigation Vision System Initialized")
        print(f"Camera resolution: {resolution}")
        print(f"Android streaming: {'Enabled' if android_streaming else 'Disabled'}")
    
    def get_navigation_mask(self, img):
        """Returns a binary mask for navigation path detection"""
        # Focus on region of interest (lower part of image)
        roi = img[self.path_roi_y_start:self.path_roi_y_end, :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Create masks for white and yellow lane markers
        white_mask = cv2.inRange(hsv, self.lane_lower_white, self.lane_upper_white)
        yellow_mask = cv2.inRange(hsv, self.lane_lower_yellow, self.lane_upper_yellow)
        
        # Combine masks for comprehensive lane detection
        lane_mask = cv2.bitwise_or(white_mask, yellow_mask)
        
        # Apply morphological operations to improve path detection
        kernel = np.ones((7, 7), np.uint8)
        lane_mask = cv2.morphologyEx(lane_mask, cv2.MORPH_CLOSE, kernel)
        lane_mask = cv2.morphologyEx(lane_mask, cv2.MORPH_OPEN, kernel)
        
        # Create full-size mask
        full_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
        full_mask[self.path_roi_y_start:self.path_roi_y_end, :] = lane_mask
        
        return full_mask, lane_mask
    
    def find_navigation_path(self, mask):
        """Finds the optimal navigation path from the mask"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        
        # Filter contours by area to remove noise
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 500]
        if not valid_contours:
            return None, None
        
        # Find the largest contour (main path)
        main_path = max(valid_contours, key=cv2.contourArea)
        
        # Calculate path center and direction
        path_moments = cv2.moments(main_path)
        if path_moments["m00"] == 0:
            return main_path, None
        
        # Calculate centroid
        cx = int(path_moments["m10"] / path_moments["m00"])
        cy = int(path_moments["m01"] / path_moments["m00"]) + self.path_roi_y_start
        
        return main_path, (cx, cy)
    
    def detect_traffic_lights(self, frame, hue_ranges, sat_min=100, val_min=100, min_area=50, max_area=5000):
        """Detect traffic lights using HSV color space and contour analysis"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lights = []
        
        # Process each hue range (e.g., red or green)
        for hue_range in hue_ranges:
            # Create mask for the hue range
            mask = cv2.inRange(hsv, (hue_range[0], sat_min, val_min), (hue_range[1], 255, 255))
            # Apply morphological operations to reduce noise
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    # Ensure aspect ratio is reasonable for traffic lights (roughly circular/square)
                    aspect_ratio = w / h if h > 0 else 1
                    if 0.5 < aspect_ratio < 2.0:
                        # Calculate average intensity in the region
                        region = hsv[y:y+h, x:x+w]
                        mask_region = mask[y:y+h, x:x+w]
                        intensity = np.sum(mask_region) / (255 * w * h) if w * h > 0 else 0
                        if intensity > 0.2:  # Threshold for strong detection
                            lights.append({
                                'bbox': (x, y, w, h),
                                'intensity': intensity,
                                'color': hue_range[2]  # Label as 'red' or 'green'
                            })
        
        return lights
    
    def track_lights(self, prev_lights, new_lights, max_distance=50):
        """Track and refine detected lights across frames"""
        if not prev_lights:
            return new_lights, new_lights
        
        tracked_lights = []
        used_new = set()
        
        for prev in prev_lights:
            prev_x, prev_y, prev_w, prev_h = prev['bbox']
            prev_center = (prev_x + prev_w // 2, prev_y + prev_h // 2)
            min_dist = float('inf')
            best_match = None
            
            for i, new_light in enumerate(new_lights):
                if i in used_new:
                    continue
                new_x, new_y, new_w, new_h = new_light['bbox']
                new_center = (new_x + new_w // 2, new_y + new_h // 2)
                dist = np.sqrt((prev_center[0] - new_center[0])**2 + (prev_center[1] - new_center[1])**2)
                
                if dist < min_dist and dist < max_distance and prev['color'] == new_light['color']:
                    min_dist = dist
                    best_match = i
            
            if best_match is not None:
                tracked_lights.append(new_lights[best_match])
                used_new.add(best_match)
        
        # Add new lights that weren't matched
        for i, new_light in enumerate(new_lights):
            if i not in used_new:
                tracked_lights.append(new_light)
        
        return tracked_lights, new_lights
    
    def detect_speed_limit(self, frame):
        """Detect speed limit signs in the frame"""
        output = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Red mask (for the outer circle)
        mask1 = cv2.inRange(hsv, self.speed_red_lower, self.speed_red_upper)
        mask2 = cv2.inRange(hsv, self.speed_red_lower2, self.speed_red_upper2)
        red_mask = cv2.bitwise_or(mask1, mask2)
        
        # White mask (for the inner circle)
        white_mask = cv2.inRange(hsv, self.speed_white_lower, self.speed_white_upper)
        
        # Black mask (for the text/numbers)
        black_mask = cv2.inRange(hsv, self.speed_black_lower, self.speed_black_upper)
        
        # Apply morphological operations to clean up masks
        kernel = np.ones((5, 5), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours in red mask
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Current frame detection status
        current_detection = False
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1000:  # Filter small contours
                continue
                
            # Check circularity
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            if circularity < 0.5:  # Relaxed circularity check
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h
            if aspect_ratio < 0.7 or aspect_ratio > 1.3:  # Relaxed aspect ratio check
                continue
                
            # Check if there's white inside the red contour
            mask_roi = white_mask[y:y+h, x:x+w]
            white_area = cv2.countNonZero(mask_roi)
            if white_area < 0.3 * area:
                continue
                
            # Check if there's black text inside the white area
            black_roi = black_mask[y:y+h, x:x+w]
            black_area = cv2.countNonZero(black_roi)
            if black_area < 0.05 * area:
                continue
                
            # Draw rectangle around the sign
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(output, "Speed Limit: 30", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
            # Add confidence percentage
            confidence_text = f"{int(self.speed_limit_confidence * 100)}%"
            cv2.putText(output, confidence_text, (x, y + h + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mark as detected in this frame
            current_detection = True
        
        # Update detection history
        self.speed_limit_history.append(current_detection)
        if len(self.speed_limit_history) > self.history_length:
            self.speed_limit_history.pop(0)
            
        # Apply temporal filtering (majority vote)
        if self.speed_limit_history:
            # Count occurrences of detection
            detection_count = sum(self.speed_limit_history)
            
            # Calculate confidence
            self.speed_limit_confidence = detection_count / len(self.speed_limit_history)
            
            # Update detection state if confidence is high enough
            if self.speed_limit_confidence > 0.6:  # More than 60% of recent frames show detection
                self.speed_limit_detected = True
            else:
                self.speed_limit_detected = False
        
        return output, red_mask, white_mask, black_mask
    
    def detect_stop_sign(self, frame):
        """Detect partial stop signs in the frame with relaxed parameters"""
        output = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Red color mask
        mask1 = cv2.inRange(hsv, self.stop_red_lower1, self.stop_red_upper1)
        mask2 = cv2.inRange(hsv, self.stop_red_lower2, self.stop_red_upper2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Current frame detection status
        current_detection = False

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1000:  # Reduced minimum area for better detection
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            # Accept polygons with 5 to 8 sides (partial octagons)
            if 5 <= len(approx) <= 8:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                
                # Relaxed aspect ratio check (stop sign roughly square)
                if 0.6 <= aspect_ratio <= 1.4:
                    hull = cv2.convexHull(cnt)
                    hull_area = cv2.contourArea(hull)
                    solidity = float(area) / hull_area if hull_area != 0 else 0
                    
                    # Relaxed solidity check
                    if solidity >= 0.75:
                        cv2.drawContours(output, [approx], -1, (0, 255, 0), 4)
                        cv2.putText(output, "STOP SIGN", (x, y - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
                        
                        # Add confidence percentage
                        confidence_text = f"{int(self.stop_detection_confidence * 100)}%"
                        cv2.putText(output, confidence_text, (x, y + h + 20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
                        # Mark as detected in this frame
                        current_detection = True

        # Update detection history
        self.stop_detection_history.append(current_detection)
        if len(self.stop_detection_history) > self.history_length:
            self.stop_detection_history.pop(0)
            
        # Apply temporal filtering (majority vote)
        if self.stop_detection_history:
            # Count occurrences of detection
            detection_count = sum(self.stop_detection_history)
            
            # Calculate confidence
            self.stop_detection_confidence = detection_count / len(self.stop_detection_history)
            
            # Update detection state if confidence is high enough
            if self.stop_detection_confidence > 0.6:  # More than 60% of recent frames show detection
                self.stop_sign_detected = True
            else:
                self.stop_sign_detected = False
        
        return output, red_mask
    
    def get_navigation_direction(self, center_x, image_center_x, threshold=40):
        """Determine navigation direction with improved sensitivity"""
        offset = center_x - image_center_x
        offset_ratio = abs(offset) / (image_center_x if image_center_x > 0 else 1)
        
        if abs(offset) < threshold:
            return "STRAIGHT"
        elif offset < -threshold:
            # More aggressive left turn detection
            return "SHARP_LEFT" if offset_ratio > 0.3 else "LEFT"
        else:
            # More aggressive right turn detection
            return "SHARP_RIGHT" if offset_ratio > 0.3 else "RIGHT"
    
    def process_navigation_frame(self, frame):
        """Process frame for navigation with Android app integration"""
        # Create output frame for visualization
        output = frame.copy()
        
        # Skip processing for performance if needed
        self.frame_skip_counter += 1
        if self.frame_skip_counter % self.skip_frames != 0:
            return output, self.navigation_data
        
        # Get navigation mask and path
        full_mask, roi_mask = self.get_navigation_mask(frame)
        main_path, path_center = self.find_navigation_path(roi_mask)
        
        # Default values
        detected_direction = "STRAIGHT"
        path_clear = True
        obstacle_distance = 0
        
        # Process path if found
        if main_path is not None and path_center is not None:
            # Draw path visualization
            cv2.drawContours(output, [main_path], -1, (0, 255, 0), 2)
            
            # Adjust path center for full image coordinates
            adjusted_center = (path_center[0], path_center[1])
            cv2.circle(output, adjusted_center, 8, (255, 0, 255), -1)
            
            # Calculate direction based on path center
            img_center_x = frame.shape[1] // 2
            detected_direction = self.get_navigation_direction(adjusted_center[0], img_center_x)
            
            # Draw navigation indicators
            self._draw_navigation_indicators(output, adjusted_center, img_center_x)
            
            # Check for obstacles in path
            obstacle_distance = self._detect_path_obstacles(frame, main_path)
            path_clear = obstacle_distance == 0
        
        # Apply temporal filtering
        self.lane_direction_history.append(detected_direction)
        if len(self.lane_direction_history) > self.history_length:
            self.lane_direction_history.pop(0)
        
        # Update current direction with confidence
        self._update_direction_with_confidence()
        
        # Update navigation data for Android app
        self._update_navigation_data(path_clear, obstacle_distance)
        
        # Add Android app streaming frame preparation
        if self.android_streaming:
            self.stream_frame = self._prepare_stream_frame(output)
        
        return output, self.navigation_data
    
    def get_stream_frame(self):
        """Get frame prepared for Android app streaming"""
        return self.stream_frame if self.stream_frame is not None else None
    
    def get_navigation_data(self):
        """Get current navigation data for Android app"""
        return self.navigation_data.copy()
    
    def _draw_navigation_indicators(self, output, path_center, img_center_x):
        """Draw navigation indicators on output frame"""
        # Draw center line
        cv2.line(output, (img_center_x, 0), (img_center_x, output.shape[0]), (0, 255, 255), 2)
        
        # Draw path center
        cv2.circle(output, path_center, 10, (255, 0, 255), -1)
        
        # Draw direction indicator
        offset = path_center[0] - img_center_x
        if abs(offset) > 40:
            arrow_start = (img_center_x, output.shape[0] - 50)
            if offset < 0:
                arrow_end = (img_center_x - 60, output.shape[0] - 80)
                color = (0, 0, 255)  # Red for left
            else:
                arrow_end = (img_center_x + 60, output.shape[0] - 80)
                color = (255, 0, 0)  # Blue for right
            cv2.arrowedLine(output, arrow_start, arrow_end, color, 4, tipLength=0.3)
    
    def _detect_path_obstacles(self, frame, path_contour):
        """Detect obstacles in the navigation path"""
        # Create mask for path area
        path_mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        cv2.fillPoly(path_mask, [path_contour], 255)
        
        # Convert to HSV and look for dark objects (potential obstacles)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        obstacle_mask = cv2.inRange(hsv, self.obstacle_lower_bound, self.obstacle_upper_bound)
        
        # Find obstacles within path
        path_obstacle_mask = cv2.bitwise_and(obstacle_mask, path_mask)
        contours, _ = cv2.findContours(path_obstacle_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_obstacle = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_obstacle) > self.min_obstacle_area:
                # Calculate approximate distance (pixels from bottom)
                _, _, _, h = cv2.boundingRect(largest_obstacle)
                distance_pixels = frame.shape[0] - h
                return distance_pixels
        
        return 0
    
    def _update_direction_with_confidence(self):
        """Update current direction with confidence calculation"""
        if not self.lane_direction_history:
            return
        
        # Count direction occurrences
        direction_counts = {}
        for direction in self.lane_direction_history:
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
        
        # Find most common direction
        most_common_direction = max(direction_counts, key=direction_counts.get)
        max_count = direction_counts[most_common_direction]
        
        # Calculate confidence
        self.lane_confidence = max_count / len(self.lane_direction_history)
        
        # Update direction if confidence is high enough
        if self.lane_confidence >= 0.6:
            self.current_direction = most_common_direction
    
    def _update_navigation_data(self, path_clear, obstacle_distance):
        """Update navigation data for Android app"""
        # Calculate FPS
        current_time = time.time()
        elapsed = current_time - self.start_time
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = current_time
        
        self.frame_count += 1
        
        # Update obstacle detection with temporal filtering
        self.obstacle_history.append(not path_clear)
        if len(self.obstacle_history) > self.history_length:
            self.obstacle_history.pop(0)
        
        obstacle_count = sum(self.obstacle_history)
        self.obstacle_confidence = obstacle_count / len(self.obstacle_history) if self.obstacle_history else 0
        self.obstacle_detected = self.obstacle_confidence > 0.4
        
        # Update navigation data
        self.navigation_data.update({
            'lane_direction': self.current_direction,
            'lane_confidence': round(self.lane_confidence, 2),
            'obstacle_detected': self.obstacle_detected,
            'obstacle_distance_pixels': obstacle_distance,
            'path_clear': path_clear and not self.obstacle_detected,
            'fps': round(self.fps, 1),
            'camera_active': True
        })
    
    def _prepare_stream_frame(self, frame):
        """Prepare frame for Android app streaming"""
        # Resize for streaming efficiency
        stream_height = 360
        aspect_ratio = frame.shape[1] / frame.shape[0]
        stream_width = int(stream_height * aspect_ratio)
        
        # Resize frame
        stream_frame = cv2.resize(frame, (stream_width, stream_height))
        
        # Add navigation overlay for Android app
        self._add_android_overlay(stream_frame)
        
        return stream_frame
    
    def _add_android_overlay(self, frame):
        """Add navigation overlay optimized for Android app display"""
        # Add direction indicator
        direction_text = f"Direction: {self.current_direction}"
        cv2.putText(frame, direction_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add confidence indicator
        confidence_text = f"Confidence: {int(self.lane_confidence * 100)}%"
        cv2.putText(frame, confidence_text, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add obstacle warning if detected
        if self.obstacle_detected:
            cv2.putText(frame, "OBSTACLE DETECTED!", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Add FPS counter
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(frame, fps_text, (frame.shape[1] - 120, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def cleanup(self):
        """Clean up camera resources"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()
        print("Navigation Vision System cleaned up")

if __name__ == "__main__":
    print("Complete Advanced Vision System")
    print("Press 'm' to toggle mask display")
    print("Press ESC to exit")
    system = CompleteVisionSystem()
    system.run()
