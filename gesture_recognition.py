# gesture_recognition.py
import mediapipe as mp
import cv2

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class HandGestureDetector:
    def __init__(self, max_num_hands=1, detection_confidence=0.7, tracking_confidence=0.6, smoothing_frames=3):
        self.hands = mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        
        # Gesture smoothing and confidence tracking
        self.smoothing_frames = smoothing_frames
        self.gesture_history = []
        self.confidence_threshold = 0.8
        self.last_stable_gesture = None

    def detect(self, frame):
        # Convert frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        gesture = None
        confidence = 0.0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks with better styling
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )
                raw_gesture, confidence = self._classify_gesture_with_confidence(hand_landmarks)
                gesture = self._smooth_gesture(raw_gesture, confidence)
                
        # Add gesture confidence indicator on frame
        if gesture and confidence > 0:
            cv2.putText(frame, f"{gesture} ({confidence:.1%})", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                       
        return frame, gesture

    def _classify_gesture(self, hand_landmarks):
        """
        Improved gesture classification with better finger detection and
        more specific gesture patterns for Rock-Paper-Scissors
        """
        # Landmark indices for fingertips and key joints
        tip_ids = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky tips
        pip_ids = [3, 6, 10, 14, 18]  # thumb IP, other finger PIP joints
        mcp_ids = [2, 5, 9, 13, 17]   # thumb MCP, other finger MCP joints
        
        fingers = []
        landmarks = hand_landmarks.landmark
        
        # Improved thumb detection - check both x and y relative positions
        thumb_tip = landmarks[tip_ids[0]]
        thumb_ip = landmarks[pip_ids[0]]
        thumb_mcp = landmarks[mcp_ids[0]]
        
        # Thumb is extended if tip is further from palm center than IP joint
        # Use distance from wrist (landmark 0) as reference
        wrist = landmarks[0]
        thumb_tip_dist = ((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)**0.5
        thumb_ip_dist = ((thumb_ip.x - wrist.x)**2 + (thumb_ip.y - wrist.y)**2)**0.5
        
        fingers.append(1 if thumb_tip_dist > thumb_ip_dist else 0)
        
        # Improved finger detection for index, middle, ring, pinky
        for i in range(1, 5):
            tip = landmarks[tip_ids[i]]
            pip = landmarks[pip_ids[i]]
            mcp = landmarks[mcp_ids[i]]
            
            # Finger is extended if tip is higher than both PIP and MCP joints
            # Also check that PIP is higher than MCP for better accuracy
            finger_extended = (tip.y < pip.y) and (tip.y < mcp.y) and (pip.y < mcp.y)
            fingers.append(1 if finger_extended else 0)
        
        # Enhanced gesture recognition with specific patterns
        total_fingers = sum(fingers)
        thumb, index, middle, ring, pinky = fingers
        
        # Rock: All fingers closed (fist)
        if total_fingers == 0:
            return "Rock"
        
        # Paper: All fingers extended
        elif total_fingers == 5:
            return "Paper"
        
        # Scissors: Multiple valid patterns
        elif total_fingers == 2:
            # Classic scissors: index and middle finger
            if index and middle and not ring and not pinky:
                return "Scissors"
            # Alternative scissors: index and ring finger
            elif index and ring and not middle and not pinky:
                return "Scissors"
            # Peace sign variation
            elif index and middle and not thumb and not ring and not pinky:
                return "Scissors"
        
        # Additional scissors pattern: just index and middle (ignore thumb)
        elif index and middle and not ring and not pinky:
            return "Scissors"
        
        # Rock variation: only thumb extended (still considered closed fist)
        elif total_fingers == 1 and thumb:
            return "Rock"
        
        # If no clear pattern matches, return None
        return None
    
    def _smooth_gesture(self, gesture, confidence):
        """Apply temporal smoothing to reduce gesture jitter"""
        if gesture is None:
            return self.last_stable_gesture
            
        # Add to history
        self.gesture_history.append((gesture, confidence))
        
        # Keep only recent frames
        if len(self.gesture_history) > self.smoothing_frames:
            self.gesture_history.pop(0)
            
        # If we don't have enough history, return current gesture
        if len(self.gesture_history) < self.smoothing_frames:
            return gesture
            
        # Count occurrences of each gesture in recent history
        gesture_counts = {}
        total_confidence = 0
        
        for hist_gesture, hist_confidence in self.gesture_history:
            if hist_gesture in gesture_counts:
                gesture_counts[hist_gesture] += hist_confidence
            else:
                gesture_counts[hist_gesture] = hist_confidence
            total_confidence += hist_confidence
            
        # Find most confident gesture
        if gesture_counts:
            best_gesture = max(gesture_counts.keys(), key=lambda g: gesture_counts[g])
            best_confidence = gesture_counts[best_gesture] / len(self.gesture_history)
            
            # Only update if confidence is high enough
            if best_confidence > self.confidence_threshold:
                self.last_stable_gesture = best_gesture
                return best_gesture
                
        return self.last_stable_gesture
    
    def _classify_gesture_with_confidence(self, hand_landmarks):
        """Enhanced gesture classification that returns confidence score"""
        gesture = self._classify_gesture(hand_landmarks)
        confidence = self._calculate_gesture_confidence(hand_landmarks, gesture)
        return gesture, confidence
    
    def _calculate_gesture_confidence(self, hand_landmarks, gesture):
        """Calculate confidence score for the detected gesture"""
        if gesture is None:
            return 0.0
            
        landmarks = hand_landmarks.landmark
        tip_ids = [4, 8, 12, 16, 20]
        pip_ids = [3, 6, 10, 14, 18]
        
        # Calculate finger extension clarity
        finger_clarity_scores = []
        
        for i in range(5):
            tip = landmarks[tip_ids[i]]
            pip = landmarks[pip_ids[i]]
            
            if i == 0:  # Thumb - use distance from wrist
                wrist = landmarks[0]
                tip_dist = ((tip.x - wrist.x)**2 + (tip.y - wrist.y)**2)**0.5
                pip_dist = ((pip.x - wrist.x)**2 + (pip.y - wrist.y)**2)**0.5
                clarity = abs(tip_dist - pip_dist) / max(tip_dist, pip_dist, 0.001)
            else:  # Other fingers - use vertical separation
                clarity = abs(tip.y - pip.y) / 0.1  # normalize by typical finger length
                
            finger_clarity_scores.append(min(clarity, 1.0))  # Cap at 1.0
            
        # Average clarity score
        base_confidence = sum(finger_clarity_scores) / len(finger_clarity_scores)
        
        # Gesture-specific confidence adjustments
        if gesture == "Rock":
            # Rock should have low finger extension
            extended_fingers = sum(1 for score in finger_clarity_scores if score > 0.3)
            confidence = base_confidence * (1.0 - extended_fingers * 0.2)
        elif gesture == "Paper":
            # Paper should have high finger extension for all fingers
            confidence = base_confidence * (sum(finger_clarity_scores) / 5.0)
        elif gesture == "Scissors":
            # Scissors should have clear separation between extended and folded fingers
            confidence = base_confidence * 0.9  # Slightly lower baseline for scissors
            
        return max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
