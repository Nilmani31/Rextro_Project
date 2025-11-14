# Rock • Paper • Scissors (Gesture) — Web

A minimal React + Vite frontend that uses MediaPipe Hands in the browser to play Rock–Paper–Scissors with hand gestures.

## Prerequisites
- Node.js 18+ and npm
- A webcam and browser permissions to access it

## Quick start

```powershell
cd e:\rock-paper-scissors-gesture\web
npm install
npm run dev
```
Then open the URL shown in the terminal (usually http://localhost:5173).

## Controls
- Start / Reset: press the button or hit `R`
- Stop camera: press the button or hit `Q` or `ESC`

## How it works
- Uses MediaPipe Hands (via CDN) to detect a single hand.
- Classifies simple gestures:
  - All fingers down → Rock
  - Five fingers up → Paper
  - Two fingers up → Scissors
- After a 3-second countdown, locks your last detected gesture and selects a random computer choice. Winner is displayed.

## Notes
- The video is mirrored horizontally to match typical webcam UX. Thumb heuristic assumes a right-hand orientation; if you often use the left hand, we can refine it using handedness from MediaPipe.
- For more accurate classification, consider per-finger angles and handedness-aware rules.
