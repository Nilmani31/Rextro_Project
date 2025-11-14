"""
web_server.py

Serve the Python MediaPipe/OpenCV output to the web as an MJPEG stream,
and expose simple endpoints to inspect/reset game state.
"""
import time
import threading
from typing import Optional, Generator

import cv2
from flask import Flask, Response, jsonify
from flask_cors import CORS

from gesture_recognition import HandGestureDetector
from utils import get_computer_choice, get_winner


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})


# Video and game state
cap = cv2.VideoCapture(0)
detector = HandGestureDetector()

state_lock = threading.Lock()
prev_time = time.time()
countdown = 3
game_started = False
user_choice: Optional[str] = None
computer_choice: Optional[str] = None
winner: Optional[str] = None


def draw_overlay(frame, txt: str, y: int, color=(255, 255, 255), scale=1.0, thickness=2):
    cv2.putText(frame, txt, (20, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def update_game_logic(gesture: Optional[str]):
    """Update countdown and game state based on gesture and time."""
    global prev_time, countdown, game_started, user_choice, computer_choice, winner
    now = time.time()
    with state_lock:
        if not game_started:
            if now - prev_time >= 1:
                countdown -= 1
                prev_time = now
            if countdown < 0:
                game_started = True
                user_choice = gesture
                computer_choice = get_computer_choice()
                winner = get_winner(user_choice, computer_choice)


def annotate_frame(frame, gesture: Optional[str]):
    """Draw the UI overlays onto the frame."""
    h, w = frame.shape[:2]
    with state_lock:
        if not game_started:
            draw_overlay(frame, f"Get Ready! Starting in {countdown}", 50, (255, 255, 255), 1.0, 2)
        else:
            draw_overlay(frame, f"You: {user_choice}", 50, (0, 255, 0), 1.2, 2)
            draw_overlay(frame, f"Computer: {computer_choice}", 90, (0, 255, 0), 1.2, 2)
            draw_overlay(frame, f"{winner}", 140, (255, 0, 0), 1.5, 3)

        # Live preview of current gesture before lock-in
        if not game_started:
            draw_overlay(frame, f"Gesture: {gesture or '—'}", h - 20, (255, 255, 0), 0.9, 2)


def generate_frames() -> Generator[bytes, None, None]:
    """MJPEG frame generator."""
    if not cap.isOpened():
        raise RuntimeError("Camera could not be opened")

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.02)
            continue

        # Mirror camera for natural UX
        frame = cv2.flip(frame, 1)

        # Run detector, draw landmarks, classify
        frame, gesture = detector.detect(frame)

        # Update game logic and draw overlays
        update_game_logic(gesture)
        annotate_frame(frame, gesture)

        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue
        jpg_bytes = buffer.tobytes()

        # MJPEG multipart frame
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n")


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/state')
def get_state():
    with state_lock:
        return jsonify({
            "countdown": countdown,
            "game_started": game_started,
            "user_choice": user_choice,
            "computer_choice": computer_choice,
            "winner": winner,
        })


@app.route('/reset', methods=['POST'])
def reset():
    global prev_time, countdown, game_started, user_choice, computer_choice, winner
    with state_lock:
        prev_time = time.time()
        countdown = 3
        game_started = False
        user_choice = None
        computer_choice = None
        winner = None
    return jsonify({"ok": True})


@app.route('/health')
def health():
    return jsonify({"ok": True, "camera_open": cap.isOpened()})


def _release():
    try:
        cap.release()
    except Exception:
        pass


if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
    finally:
        _release()
