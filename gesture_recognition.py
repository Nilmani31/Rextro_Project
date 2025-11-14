# gesture_recognition.py
import mediapipe as mp
import cv2

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class HandGestureDetector:
    def __init__(self, max_num_hands=1, detection_confidence=0.7, tracking_confidence=0.6):
        self.hands = mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

    def detect(self, frame):
        # Convert frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        gesture = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                gesture = self._classify_gesture(hand_landmarks)
        return frame, gesture

    def _classify_gesture(self, hand_landmarks):
        # Extract finger tip landmarks
        tips = [4, 8, 12, 16, 20]
        fingers = []

        # Thumb
        if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)

        # Other fingers
        for tip in tips[1:]:
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
                fingers.append(1)
            else:
                fingers.append(0)

        # Determine gesture
        total_fingers = sum(fingers)

        if total_fingers == 0:
            return "Rock"
        elif total_fingers == 2:
            return "Scissors"
        elif total_fingers == 5:
            return "Paper"
        else:
            return None
