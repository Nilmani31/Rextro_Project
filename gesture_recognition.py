# gesture_recognition.py
import mediapipe as mp
import cv2
import numpy as np
from collections import deque
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class HandGestureDetector:
    def __init__(self, max_num_hands=1, detection_confidence=0.8, tracking_confidence=0.7, smoothing_frames=5):
        self.hands = mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
            static_image_mode=False
        )
        
        # Enhanced smoothing system
        self.smoothing_frames = smoothing_frames
        self.gesture_history = deque(maxlen=smoothing_frames)
        self.confidence_history = deque(maxlen=smoothing_frames)
        self.last_stable_gesture = None
        self.gesture_stability_count = 0
        self.min_stability_frames = 3
        
        # Hand tracking quality
        self.hand_quality_history = deque(maxlen=10)
        self.last_detection_time = time.time()
        
        # Gesture confidence thresholds
        self.confidence_thresholds = {
            "Rock": 0.75,
            "Paper": 0.85,
            "Scissors": 0.80
        }

    def detect(self, frame):
        """Enhanced detection with quality assessment and stability checking"""
        # Flip frame for mirror effect (important for user experience)
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        
        # Process with MediaPipe
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True
        
        # Initialize variables
        gesture = None
        confidence = 0.0
        hand_quality = 0.0
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Always draw basic MediaPipe landmarks first for visibility
                mp_drawing.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=3),  # White dots
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)  # Red lines
                )
                
                # Assess hand detection quality
                hand_quality = self._assess_hand_quality(hand_landmarks)
                self.hand_quality_history.append(hand_quality)
                
                # Always try to classify gesture, even with lower quality
                gesture, confidence = self._classify_gesture_with_confidence(hand_landmarks)
                
                # Add enhanced visual feedback if quality is good
                if hand_quality > 0.6:
                    self._draw_enhanced_landmarks(frame, hand_landmarks, hand_quality)
                
                # Add detailed hand analysis display
                self._draw_hand_analysis(frame, hand_landmarks, gesture, confidence)
                
                self.last_detection_time = time.time()
                break
        
        # Enhanced smoothing and stability check
        stable_gesture = self._apply_advanced_smoothing(gesture, confidence)
        
        # Display comprehensive feedback
        self._draw_detection_feedback(frame, stable_gesture, hand_quality)
        
        return frame, stable_gesture

    def _assess_hand_quality(self, hand_landmarks):
        """Assess the quality of hand detection"""
        landmarks = hand_landmarks.landmark
        
        # Check landmark visibility and consistency
        visibility_scores = []
        for landmark in landmarks:
            if hasattr(landmark, 'visibility'):
                visibility_scores.append(landmark.visibility)
        
        # Calculate hand spread (more spread = better detection)
        fingertips = [landmarks[4], landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        palm_center = landmarks[0]  # wrist
        
        total_spread = 0
        for tip in fingertips:
            spread = ((tip.x - palm_center.x)**2 + (tip.y - palm_center.y)**2)**0.5
            total_spread += spread
        
        avg_spread = total_spread / 5
        spread_quality = min(avg_spread * 5, 1.0)  # Normalize
        
        # Check landmark stability (consistent positioning)
        stability_score = 1.0  # Default high if no visibility info
        if visibility_scores:
            stability_score = sum(visibility_scores) / len(visibility_scores)
        
        # Combined quality score
        quality = (spread_quality * 0.6) + (stability_score * 0.4)
        return min(quality, 1.0)

    def _draw_enhanced_landmarks(self, frame, hand_landmarks, quality):
        """Draw enhanced landmarks with quality-based styling (in addition to basic ones)"""
        # Add quality-based bounding box
        self._draw_quality_bounding_box(frame, hand_landmarks, quality)
        
        # Add fingertip highlights for better visibility
        h, w, _ = frame.shape
        fingertips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
        
        for tip_id in fingertips:
            tip = hand_landmarks.landmark[tip_id]
            x, y = int(tip.x * w), int(tip.y * h)
            
            # Color based on quality
            if quality > 0.8:
                color = (0, 255, 0)      # Green - Excellent
            elif quality > 0.6:
                color = (0, 255, 255)    # Yellow - Good  
            else:
                color = (0, 100, 255)    # Orange - Needs improvement
            
            # Draw larger circles on fingertips
            cv2.circle(frame, (x, y), 8, color, -1)
            cv2.circle(frame, (x, y), 10, (255, 255, 255), 2)

    def _draw_quality_bounding_box(self, frame, hand_landmarks, quality):
        """Draw bounding box with quality color coding"""
        h, w, _ = frame.shape
        x_coords = [lm.x * w for lm in hand_landmarks.landmark]
        y_coords = [lm.y * h for lm in hand_landmarks.landmark]
        
        x_min, x_max = int(min(x_coords)) - 20, int(max(x_coords)) + 20
        y_min, y_max = int(min(y_coords)) - 20, int(max(y_coords)) + 20
        
        # Color based on quality
        if quality > 0.8:
            box_color = (0, 255, 0)      # Green - Excellent
        elif quality > 0.6:
            box_color = (0, 255, 255)    # Yellow - Good
        else:
            box_color = (0, 100, 255)    # Orange - Needs improvement
        
        # Draw bounding box
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), box_color, 2)
        
        # Add quality indicator
        quality_text = f"Quality: {quality:.1%}"
        cv2.putText(frame, quality_text, (x_min, y_min - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

    def _draw_hand_analysis(self, frame, hand_landmarks, gesture, confidence):
        """Draw detailed hand analysis information"""
        landmarks = hand_landmarks.landmark
        h, w, _ = frame.shape
        
        # Get finger states for debugging
        fingers = self._get_advanced_finger_states(landmarks)
        finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        
        # Display finger states on the right side
        y_start = 50
        for i, (name, state) in enumerate(zip(finger_names, fingers)):
            color = (0, 255, 0) if state else (0, 0, 255)
            text = f"{name}: {'UP' if state else 'DOWN'}"
            cv2.putText(frame, text, (w - 200, y_start + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Display gesture confidence
        if gesture and confidence > 0:
            conf_text = f"Confidence: {confidence:.1%}"
            conf_color = (0, 255, 0) if confidence > 0.8 else (0, 255, 255) if confidence > 0.6 else (0, 100, 255)
            cv2.putText(frame, conf_text, (w - 200, y_start + 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, conf_color, 2)

    def _classify_gesture_with_confidence(self, hand_landmarks):
        """Enhanced gesture classification with confidence scoring"""
        landmarks = hand_landmarks.landmark
        
        # Get advanced finger states
        fingers = self._get_advanced_finger_states(landmarks)
        
        # Start with simple finger counting method for reliability
        gesture = self._method_finger_counting(fingers)
        confidence = 0.8 if gesture else 0.0
        
        # If we have a gesture, validate with other methods
        if gesture:
            method2_result = self._method_distance_analysis(landmarks)
            method3_result = self._method_angle_analysis(landmarks)
            
            # Boost confidence if multiple methods agree
            if method2_result == gesture:
                confidence += 0.1
            if method3_result == gesture:
                confidence += 0.1
                
            confidence = min(confidence, 1.0)
        
        # Lower threshold for better responsiveness
        min_confidence = 0.6
        if confidence < min_confidence:
            return None, 0.0
        
        return gesture, confidence

    def _get_advanced_finger_states(self, landmarks):
        """Advanced finger state detection with orientation awareness"""
        fingers = []
        
        # Detect hand orientation
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        index_base = landmarks[5]
        pinky_base = landmarks[17]
        
        # Calculate orientation vectors
        vertical_dist = abs(middle_tip.y - wrist.y)
        horizontal_dist = abs(middle_tip.x - wrist.x)
        is_vertical = vertical_dist > horizontal_dist * 1.2
        
        # Thumb detection (orientation-aware)
        thumb_tip = landmarks[4]
        thumb_pip = landmarks[3]
        thumb_mcp = landmarks[2]
        
        if is_vertical:
            # Vertical hand: use X-axis for thumb
            thumb_extended = abs(thumb_tip.x - thumb_mcp.x) > 0.06
        else:
            # Horizontal hand: use distance-based approach
            thumb_extended = ((thumb_tip.x - thumb_mcp.x)**2 + (thumb_tip.y - thumb_mcp.y)**2)**0.5 > 0.08
        
        fingers.append(1 if thumb_extended else 0)
        
        # Other fingers (adaptive detection)
        finger_tips = [8, 12, 16, 20]   # index, middle, ring, pinky tips
        finger_pips = [6, 10, 14, 18]   # PIP joints
        finger_mcps = [5, 9, 13, 17]    # MCP joints
        
        for tip_id, pip_id, mcp_id in zip(finger_tips, finger_pips, finger_mcps):
            tip = landmarks[tip_id]
            pip = landmarks[pip_id]
            mcp = landmarks[mcp_id]
            
            if is_vertical:
                # Vertical: Y-axis check with stricter threshold
                finger_up = tip.y < pip.y - 0.015
            else:
                # Horizontal: distance-based check
                tip_dist = ((tip.x - mcp.x)**2 + (tip.y - mcp.y)**2)**0.5
                pip_dist = ((pip.x - mcp.x)**2 + (pip.y - mcp.y)**2)**0.5
                finger_up = tip_dist > pip_dist * 1.4
            
            fingers.append(1 if finger_up else 0)
        
        return fingers

    def _method_finger_counting(self, fingers):
        """Traditional finger counting method"""
        total_fingers = sum(fingers)
        thumb, index, middle, ring, pinky = fingers
        
        # Paper - open hand (4-5 fingers)
        if total_fingers >= 4:
            return "Paper"
        
        # Scissors - index and middle up, others down
        elif index and middle and not ring and not pinky and total_fingers == 2:
            return "Scissors"
        
        # Rock - closed fist (0-2 fingers)
        elif total_fingers <= 2:
            return "Rock"
        
        return None

    def _method_distance_analysis(self, landmarks):
        """Distance-based gesture analysis"""
        wrist = landmarks[0]
        fingertips = [landmarks[4], landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        
        # Calculate average distance from wrist
        distances = [
            ((tip.x - wrist.x)**2 + (tip.y - wrist.y)**2)**0.5 
            for tip in fingertips
        ]
        avg_distance = sum(distances) / len(distances)
        
        # Calculate finger spread
        spreads = []
        for i in range(len(fingertips) - 1):
            spread = ((fingertips[i].x - fingertips[i+1].x)**2 + 
                     (fingertips[i].y - fingertips[i+1].y)**2)**0.5
            spreads.append(spread)
        avg_spread = sum(spreads) / len(spreads) if spreads else 0
        
        # Gesture classification based on distances
        if avg_distance > 0.25 and avg_spread > 0.08:
            return "Paper"  # Large distance, high spread
        elif avg_distance > 0.20 and avg_spread < 0.05:
            # Check for scissors pattern
            index_middle_dist = ((fingertips[1].x - fingertips[2].x)**2 + 
                               (fingertips[1].y - fingertips[2].y)**2)**0.5
            if index_middle_dist < 0.08:  # Index and middle close together
                return "Scissors"
        elif avg_distance < 0.18:
            return "Rock"  # Small distance = closed fist
        
        return None

    def _method_angle_analysis(self, landmarks):
        """Angle-based gesture analysis"""
        def calculate_angle(p1, p2, p3):
            """Calculate angle between three points"""
            v1 = np.array([p1.x - p2.x, p1.y - p2.y])
            v2 = np.array([p3.x - p2.x, p3.y - p2.y])
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            return np.degrees(angle)
        
        # Calculate finger bend angles
        finger_angles = []
        finger_joints = [
            [5, 6, 8],   # Index: MCP -> PIP -> TIP
            [9, 10, 12], # Middle: MCP -> PIP -> TIP
            [13, 14, 16], # Ring: MCP -> PIP -> TIP
            [17, 18, 20]  # Pinky: MCP -> PIP -> TIP
        ]
        
        for mcp_id, pip_id, tip_id in finger_joints:
            angle = calculate_angle(landmarks[mcp_id], landmarks[pip_id], landmarks[tip_id])
            finger_angles.append(angle)
        
        # Classify based on angles
        extended_count = sum(1 for angle in finger_angles if angle > 160)  # Nearly straight
        bent_count = sum(1 for angle in finger_angles if angle < 120)     # Significantly bent
        
        if extended_count >= 3:
            return "Paper"
        elif extended_count == 2 and finger_angles[0] > 160 and finger_angles[1] > 160:
            return "Scissors"  # Index and middle extended
        elif bent_count >= 3:
            return "Rock"
        
        return None

    def _apply_advanced_smoothing(self, current_gesture, confidence):
        """Advanced smoothing with confidence weighting"""
        if current_gesture and confidence > 0.5:
            self.gesture_history.append(current_gesture)
            self.confidence_history.append(confidence)
        
        if len(self.gesture_history) < 2:
            return self.last_stable_gesture
        
        # Weighted voting based on confidence
        gesture_scores = {}
        for gesture, conf in zip(self.gesture_history, self.confidence_history):
            gesture_scores[gesture] = gesture_scores.get(gesture, 0) + conf
        
        if gesture_scores:
            best_gesture = max(gesture_scores, key=gesture_scores.get)
            best_score = gesture_scores[best_gesture]
            
            # Require minimum confidence and consistency
            if best_score > 2.0 and list(self.gesture_history)[-2:].count(best_gesture) >= 2:
                if best_gesture != self.last_stable_gesture:
                    self.gesture_stability_count = 1
                    self.last_stable_gesture = best_gesture
                else:
                    self.gesture_stability_count += 1
                
                return self.last_stable_gesture
        
        return self.last_stable_gesture

    def _draw_detection_feedback(self, frame, gesture, hand_quality):
        """Draw comprehensive detection feedback"""
        h, w, _ = frame.shape
        
        # Main gesture display
        if gesture:
            # Large gesture text with color coding
            gesture_color = {
                "Rock": (0, 100, 255),     # Orange
                "Paper": (0, 255, 0),      # Green
                "Scissors": (255, 0, 0)    # Blue
            }.get(gesture, (255, 255, 255))
            
            cv2.putText(frame, f"Gesture: {gesture}", (10, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, gesture_color, 3)
            
            # Stability indicator
            stability_text = f"Stability: {self.gesture_stability_count}/{self.min_stability_frames}"
            stability_color = (0, 255, 0) if self.gesture_stability_count >= self.min_stability_frames else (0, 255, 255)
            cv2.putText(frame, stability_text, (10, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, stability_color, 2)
        else:
            # No detection feedback
            time_since_detection = time.time() - self.last_detection_time
            if time_since_detection < 2:
                cv2.putText(frame, "Analyzing hand...", (10, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            else:
                cv2.putText(frame, "No hand detected", (10, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Hand quality indicator
        if hand_quality > 0:
            quality_color = (0, 255, 0) if hand_quality > 0.8 else (0, 255, 255) if hand_quality > 0.6 else (0, 100, 255)
            cv2.putText(frame, f"Hand Quality: {hand_quality:.1%}", (10, h - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, quality_color, 2)
        
        # Detection tips
        tip_text = "Tips: Keep hand visible, avoid quick movements"
        cv2.putText(frame, tip_text, (10, h - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)