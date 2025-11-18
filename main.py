# main.py
import cv2
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import numpy as np
from gesture_recognition import HandGestureDetector
from utils import get_computer_choice, get_winner, GameManager

# Shared state for HTTP streaming
latest_jpeg = b""  # last encoded annotated frame
state_lock = threading.Lock()
HTTP_PORT = 5002

# Enhanced Game state with 3-round system
game_manager = GameManager()
armed = False  # set to True to start countdown via web button
prev_time = 0.0
countdown = 3
game_started = False
user_choice = None
computer_choice = None
winner = None
round_result = None

class StreamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # silence default logging
        return

    def _send_headers(self, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_headers(200, "application/json")
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
        elif self.path == "/state":
            global armed, countdown, game_started, user_choice, computer_choice, winner, round_result, game_manager
            with state_lock:
                game_status = game_manager.get_game_status()
                payload = {
                    "armed": armed,
                    "countdown": countdown,
                    "game_started": game_started,
                    "user_choice": user_choice,
                    "computer_choice": computer_choice,
                    "winner": winner,
                    "round_result": round_result,
                    "game_status": game_status
                }
            self._send_headers(200, "application/json")
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        elif self.path == "/start":  # allow GET for simplicity
            self._handle_start()
        elif self.path.startswith("/difficulty/"):
            self._handle_difficulty()
        elif self.path == "/reset":
            self._handle_reset()
        elif self.path == "/frame":
            # Single JPEG for quick testing
            global latest_jpeg
            self._send_headers(200, "image/jpeg")
            self.wfile.write(latest_jpeg)
        elif self.path == "/video_feed":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                while True:
                    frame_bytes = latest_jpeg
                    if frame_bytes:
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
        else:
            self._send_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

    def do_OPTIONS(self):  # CORS preflight support
        self._send_headers(200)

    def do_POST(self):
        if self.path == "/start":
            self._handle_start()
        elif self.path.startswith("/difficulty/"):
            self._handle_difficulty()
        elif self.path == "/reset":
            self._handle_reset()
        else:
            self._send_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "not found"}).encode("utf-8"))

    def _handle_start(self):
        global armed, prev_time, countdown, game_started, user_choice, computer_choice, winner, round_result
        with state_lock:
            armed = True
            prev_time = time.time()
            countdown = 3
            game_started = False
            user_choice = None
            computer_choice = None
            winner = None
            round_result = None
        self._send_headers(200, "application/json")
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
    
    def _handle_difficulty(self):
        global game_manager
        difficulty = self.path.split("/")[-1].capitalize()
        with state_lock:
            success = game_manager.set_difficulty(difficulty)
        
        self._send_headers(200, "application/json")
        self.wfile.write(json.dumps({"success": success, "difficulty": difficulty}).encode("utf-8"))
    
    def _handle_reset(self):
        global game_manager, armed, game_started, user_choice, computer_choice, winner, round_result
        with state_lock:
            game_manager.reset_game()
            armed = False
            game_started = False
            user_choice = None
            computer_choice = None
            winner = None
            round_result = None
        
        self._send_headers(200, "application/json")
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

def start_http_server():
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), StreamHandler)
    print(f"[stream] MJPEG server running at http://127.0.0.1:{HTTP_PORT}/video_feed")
    server.serve_forever()

def main():
    def make_placeholder(text_lines=None, size=(480, 640)):
        if text_lines is None:
            text_lines = [
                "Camera not available",
                "Ensure no other app is using it",
                f"Open: http://127.0.0.1:{HTTP_PORT}/health",
            ]
        h, w = size
        img = np.zeros((h, w, 3), dtype=np.uint8)
        y = 40
        for line in text_lines:
            cv2.putText(img, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y += 35
        return img

    def encode_and_set(img):
        global latest_jpeg
        try:
            ret_jpg, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret_jpg:
                latest_jpeg = buf.tobytes()
        except Exception:
            pass

    # Preload a placeholder so /video_feed has something immediately
    encode_and_set(make_placeholder())

    def open_camera():
        # Prefer DirectShow on Windows; fallback to default
        cap_try = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap_try.isOpened():
            cap_try.release()
            cap_try = cv2.VideoCapture(0)
        return cap_try

    cap = open_camera()
    detector = HandGestureDetector()
    global prev_time, countdown, game_started, user_choice, computer_choice, winner, armed
    # Initial idle state until user presses Start in web UI
    with state_lock:
        armed = False
        prev_time = time.time()
        countdown = 3
        game_started = False
        user_choice = None
        computer_choice = None
        winner = None

    # Start HTTP streaming server thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    show_window = os.getenv("RPS_SHOW_WINDOW", "1") != "0"

    while True:
        ret, frame = cap.read()
        if not ret:
            # Attempt to re-open camera and serve placeholder
            cap.release()
            cap = open_camera()
            placeholder = make_placeholder()
            encode_and_set(placeholder)
            if show_window:
                try:
                    cv2.imshow("Rock Paper Scissors", placeholder)
                except Exception:
                    pass
            time.sleep(0.1)
            key = cv2.waitKey(1) if show_window else -1
            if key == 27 or key == ord('q'):
                break
            continue

        frame = cv2.flip(frame, 1)  # Mirror camera
        frame, gesture = detector.detect(frame)

        h, w, _ = frame.shape

        # Countdown before result (only when armed via web button)
        if not game_started:
            if not armed:
                cv2.putText(frame, "Click Start in web UI to begin", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            else:
                cv2.putText(frame, f"Get Ready! Starting in {countdown}", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                if time.time() - prev_time >= 1:
                    countdown -= 1
                    prev_time = time.time()

                if countdown < 0:
                    game_started = True
                    user_choice = gesture
                    computer_choice = game_manager.get_computer_choice()
                    round_result = game_manager.play_round(user_choice, computer_choice)
                    winner = get_winner(user_choice, computer_choice)
        else:
            # Display current round info
            game_status = game_manager.get_game_status()
            cv2.putText(frame, f"Level: {game_status['level']} | Round: {game_status['round']}/{game_status['max_rounds']}", 
                        (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"Score: {game_status['player_score']}-{game_status['computer_score']}", 
                        (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"You: {user_choice}", (50, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            cv2.putText(frame, f"Computer: {computer_choice}", (50, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            cv2.putText(frame, winner, (50, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 2)
            
            # Show final game result if completed
            if game_status['game_completed']:
                cv2.putText(frame, game_status['game_winner'], (50, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)

        # Encode current annotated frame for HTTP streaming
        encode_and_set(frame)

        if show_window:
            try:
                cv2.imshow("Rock Paper Scissors", frame)
            except Exception:
                pass

        key = cv2.waitKey(1) if show_window else -1
        if key == ord('r'):
            with state_lock:
                if game_manager.game_completed:
                    # Reset for new game
                    game_manager.reset_game()
                    user_choice = None
                    computer_choice = None
                    winner = None
                    round_result = None
                armed = True
                countdown = 3
                game_started = False
                prev_time = time.time()
        elif key == 27 or key == ord('q'):  # ESC or 'q' to quit
            break

    cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

if __name__ == "__main__":
    main()