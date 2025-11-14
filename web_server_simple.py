"""web_server_simple.py

Pure Python (stdlib only) HTTP server that streams the MediaPipe/OpenCV
output as MJPEG and exposes JSON game state endpoints. No Flask needed.

Endpoints:
  /video_feed  -> multipart/x-mixed-replace MJPEG stream
  /state       -> JSON game state
  /reset       -> POST to reset game

Run:
  python web_server_simple.py

Then open the React frontend (already pointing to http://127.0.0.1:5000). If you
changed the port, update Home.jsx accordingly.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import cv2
from gesture_recognition import HandGestureDetector
from utils import get_computer_choice, get_winner


HOST = "0.0.0.0"  # bind all interfaces for easier access
PORT = 5001

cap = cv2.VideoCapture(0)
detector = HandGestureDetector()

state_lock = threading.Lock()
prev_time = time.time()
countdown = 3
game_started = False
user_choice = None
computer_choice = None
winner = None
latest_jpeg = b""  # cached latest encoded frame

def update_game_logic(gesture):
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

def annotate_frame(frame, gesture):
    h, _ = frame.shape[:2]
    with state_lock:
        if not game_started:
            cv2.putText(frame, f"Get Ready! Starting in {countdown}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255),2)
        else:
            cv2.putText(frame, f"You: {user_choice}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0),2)
            cv2.putText(frame, f"Computer: {computer_choice}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0),2)
            cv2.putText(frame, f"{winner}", (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,0,0),3)
        if not game_started:
            cv2.putText(frame, f"Gesture: {gesture or '—'}", (20, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,0),2)

def capture_loop():
    global latest_jpeg
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.02)
            continue
        frame = cv2.flip(frame, 1)
        frame, gesture = detector.detect(frame)
        update_game_logic(gesture)
        annotate_frame(frame, gesture)
        ret, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ret:
            latest_jpeg = buf.tobytes()
        time.sleep(0.01)  # small pause

def _placeholder_jpeg(width=640, height=480):
    img = cv2.imread('')  # always None
    if img is None:
        import numpy as np
        img = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(img, 'Initializing stream...', (20, height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (200,200,200), 2)
    ret, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return buf.tobytes() if ret else b''

class Handler(BaseHTTPRequestHandler):
    server_version = "RPSGestureSimple/0.1"

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):  # CORS preflight
        self._set_headers()

    def do_GET(self):
        if self.path == "/state":
            with state_lock:
                payload = {
                    "countdown": countdown,
                    "game_started": game_started,
                    "user_choice": user_choice,
                    "computer_choice": computer_choice,
                    "winner": winner,
                }
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        elif self.path == "/frame":
            # Return single JPEG frame for simpler testing
            frame_bytes = latest_jpeg or _placeholder_jpeg()
            self._set_headers(200, "image/jpeg")
            self.wfile.write(frame_bytes)
        elif self.path == "/video_feed":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
            self.end_headers()
            try:
                while True:
                    frame_bytes = latest_jpeg or _placeholder_jpeg()
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b"\r\n")
                    try:
                        self.wfile.flush()
                    except Exception:
                        pass
                    time.sleep(0.05)
            except ConnectionResetError:
                pass
        elif self.path == "/health":
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ok": True, "camera_open": cap.isOpened()}).encode("utf-8"))
        else:
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

    def do_POST(self):
        if self.path == "/reset":
            global prev_time, countdown, game_started, user_choice, computer_choice, winner
            with state_lock:
                prev_time = time.time()
                countdown = 3
                game_started = False
                user_choice = None
                computer_choice = None
                winner = None
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
        else:
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

def main():
    if not cap.isOpened():
        raise RuntimeError("Camera not available")
    t = threading.Thread(target=capture_loop, daemon=True)
    t.start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[web_server_simple] Serving on http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    finally:
        cap.release()

if __name__ == "__main__":
    main()
