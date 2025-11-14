import React, { useState } from 'react'

export default function Home() {
	const [error, setError] = useState('')

	return (
		<div style={{ padding: 16 }}>
			<h1>Rock • Paper • Scissors — Gesture</h1>
			<p>Below is the live screen coming from the Python app (MediaPipe + OpenCV).</p>

			<div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
				<button onClick={async () => {
					try {
						await fetch('http://127.0.0.1:5002/start', { method: 'POST' })
					} catch {}
				}}>Start Game</button>
			</div>

			<div style={{
				position: 'relative',
				width: '100%',
				maxWidth: 960,
				aspectRatio: '4 / 3',
				borderRadius: 8,
				overflow: 'hidden',
				background: '#111'
			}}>
										<img
											src="http://127.0.0.1:5002/video_feed"
					alt="Python Gesture Stream"
											onError={() => setError('Can\'t reach the Python stream at http://127.0.0.1:5002/video_feed')}
					style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}
				/>
										{/* Fallback test link for single frame */}
										<a href="http://127.0.0.1:5002/frame" target="_blank" rel="noreferrer" style={{position:'absolute', right:8, bottom:8, background:'#0008', color:'#fff', padding:'6px 8px', borderRadius:6, textDecoration:'none', fontSize:12}}>Test single frame</a>
			</div>

			{error && (
				<div style={{ marginTop: 12, color: '#b91c1c' }}>
					{error}
				</div>
			)}

			<div style={{ marginTop: 12, fontSize: 14, opacity: 0.8 }}>
				Tip: Make sure the Python server is running. In another terminal:
				<pre style={{ background: '#0b0b0b', padding: 8, borderRadius: 6 }}>
{`cd e:\\rock-paper-scissors-gesture
.\\.venv\\Scripts\\python.exe main.py`}
				</pre>
			</div>
		</div>
	)
}
