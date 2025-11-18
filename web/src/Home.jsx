import React, { useState, useEffect } from 'react'

export default function Home() {
	const [error, setError] = useState('')
	const [gameState, setGameState] = useState(null)
	const [selectedDifficulty, setSelectedDifficulty] = useState('Easy')
	const [currentPage, setCurrentPage] = useState('welcome') // welcome, difficulty, gameplay, results

	// Poll game state
	useEffect(() => {
		const interval = setInterval(async () => {
			try {
				const response = await fetch('http://127.0.0.1:5002/state')
				if (response.ok) {
					const data = await response.json()
					setGameState(data)
					
					// Auto-navigate based on game state
					if (data.game_status?.game_completed && currentPage === 'gameplay') {
						setCurrentPage('results')
					}
				}
			} catch (err) {
				// Silent fail
			}
		}, 1000)

		return () => clearInterval(interval)
	}, [currentPage])

	const startGame = async () => {
		try {
			await fetch('http://127.0.0.1:5002/start', { method: 'POST' })
		} catch {}
	}

	const setDifficulty = async (level) => {
		try {
			await fetch(`http://127.0.0.1:5002/difficulty/${level.toLowerCase()}`, { method: 'POST' })
			setSelectedDifficulty(level)
		} catch {}
	}

	const resetGame = async () => {
		try {
			await fetch('http://127.0.0.1:5002/reset', { method: 'POST' })
			setCurrentPage('welcome')
		} catch {}
	}

	// Page Components
	const WelcomePage = () => (
		<div style={{
			display: 'flex',
			flexDirection: 'column',
			alignItems: 'center',
			justifyContent: 'center',
			minHeight: '100vh',
			background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
			color: 'white',
			textAlign: 'center',
			padding: 20
		}}>
			<div style={{
				background: 'rgba(255,255,255,0.1)',
				borderRadius: 20,
				padding: 40,
				backdropFilter: 'blur(10px)',
				border: '1px solid rgba(255,255,255,0.2)'
			}}>
				<h1 style={{ fontSize: 48, marginBottom: 20, textShadow: '2px 2px 4px rgba(0,0,0,0.3)' }}>
					🎮 Rock Paper Scissors
				</h1>
				<h2 style={{ fontSize: 24, marginBottom: 30, opacity: 0.9 }}>
					Gesture Recognition Challenge
				</h2>
				<p style={{ fontSize: 18, marginBottom: 40, maxWidth: 600 }}>
					Use your hand gestures to play against intelligent AI opponents!
					Master 3 rounds to become the champion.
				</p>
				<button
					onClick={() => setCurrentPage('difficulty')}
					style={{
						fontSize: 20,
						padding: '15px 40px',
						border: 'none',
						borderRadius: 50,
						background: 'linear-gradient(45deg, #ff6b6b, #ee5a24)',
						color: 'white',
						cursor: 'pointer',
						boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
						transition: 'transform 0.2s',
						fontWeight: 'bold'
					}}
					onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
					onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
				>
					🚀 Start Your Challenge
				</button>
			</div>
		</div>
	)

	const DifficultyPage = () => (
		<div style={{
			display: 'flex',
			flexDirection: 'column',
			alignItems: 'center',
			justifyContent: 'center',
			minHeight: '100vh',
			background: 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
			color: 'white',
			textAlign: 'center',
			padding: 20
		}}>
			<div style={{
				background: 'rgba(255,255,255,0.1)',
				borderRadius: 20,
				padding: 40,
				backdropFilter: 'blur(10px)',
				border: '1px solid rgba(255,255,255,0.2)',
				maxWidth: 800
			}}>
				<h1 style={{ fontSize: 36, marginBottom: 30 }}>Choose Your Challenge Level</h1>
				
				<div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 40 }}>
					{[
						{ level: 'Easy', emoji: '🟢', desc: 'Random AI - Perfect for beginners', color: '#00b894' },
						{ level: 'Medium', emoji: '🟡', desc: 'Adaptive AI - Learns your patterns', color: '#fdcb6e' },
						{ level: 'Hard', emoji: '🔴', desc: 'Predictive AI - Advanced strategy', color: '#e17055' }
					].map(({ level, emoji, desc, color }) => (
						<div
							key={level}
							onClick={() => setDifficulty(level)}
							style={{
								padding: 20,
								borderRadius: 15,
								background: selectedDifficulty === level ? color : 'rgba(255,255,255,0.1)',
								border: `3px solid ${selectedDifficulty === level ? 'white' : 'transparent'}`,
								cursor: 'pointer',
								transition: 'all 0.3s',
								transform: selectedDifficulty === level ? 'scale(1.05)' : 'scale(1)'
							}}
						>
							<div style={{ fontSize: 40, marginBottom: 10 }}>{emoji}</div>
							<h3 style={{ margin: 0, fontSize: 20, marginBottom: 10 }}>{level}</h3>
							<p style={{ margin: 0, fontSize: 14, opacity: 0.9 }}>{desc}</p>
						</div>
					))}
				</div>

				<div style={{ display: 'flex', gap: 20, justifyContent: 'center' }}>
					<button
						onClick={() => setCurrentPage('welcome')}
						style={{
							padding: '12px 24px',
							border: '2px solid white',
							borderRadius: 25,
							background: 'transparent',
							color: 'white',
							cursor: 'pointer',
							fontSize: 16
						}}
					>
						← Back
					</button>
					<button
						onClick={() => setCurrentPage('gameplay')}
						style={{
							padding: '12px 30px',
							border: 'none',
							borderRadius: 25,
							background: 'linear-gradient(45deg, #00b894, #00a085)',
							color: 'white',
							cursor: 'pointer',
							fontSize: 16,
							fontWeight: 'bold'
						}}
					>
						Start Game →
					</button>
				</div>
			</div>
		</div>
	)

	const GameplayPage = () => (
		<div style={{
			display: 'flex',
			flexDirection: 'column',
			minHeight: '100vh',
			background: 'linear-gradient(135deg, #2d3436 0%, #636e72 100%)',
			color: 'white'
		}}>
			{/* Header */}
			<div style={{
				padding: 20,
				background: 'rgba(0,0,0,0.3)',
				display: 'flex',
				justifyContent: 'space-between',
				alignItems: 'center'
			}}>
				<h2 style={{ margin: 0 }}>🎯 {selectedDifficulty} Mode</h2>
				{gameState?.game_status && (
					<div style={{ display: 'flex', gap: 30, alignItems: 'center' }}>
						<div style={{ textAlign: 'center' }}>
							<div style={{ fontSize: 24, fontWeight: 'bold', color: '#00b894' }}>
								{gameState.game_status.player_score}
							</div>
							<div style={{ fontSize: 12 }}>YOU</div>
						</div>
						<div style={{ fontSize: 20, opacity: 0.7 }}>
							Round {gameState.game_status.round}/{gameState.game_status.max_rounds}
						</div>
						<div style={{ textAlign: 'center' }}>
							<div style={{ fontSize: 24, fontWeight: 'bold', color: '#e17055' }}>
								{gameState.game_status.computer_score}
							</div>
							<div style={{ fontSize: 12 }}>AI</div>
						</div>
					</div>
				)}
			</div>

			{/* Main Game Area */}
			<div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
				{/* Video Feed */}
				<div style={{
					position: 'relative',
					width: '90%',
					maxWidth: 800,
					aspectRatio: '4 / 3',
					borderRadius: 15,
					overflow: 'hidden',
					border: '3px solid #74b9ff',
					boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
				}}>
					<img
						src="http://127.0.0.1:5002/video_feed"
						alt="Gesture Detection"
						onError={() => setError('Cannot connect to camera')}
						style={{ width: '100%', height: '100%', objectFit: 'cover' }}
					/>
					
					{/* Game Status Overlay */}
					{gameState?.countdown !== undefined && gameState.countdown >= 0 && (
						<div style={{
							position: 'absolute',
							top: 0,
							left: 0,
							right: 0,
							bottom: 0,
							background: 'rgba(0,0,0,0.7)',
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							fontSize: 72,
							fontWeight: 'bold',
							color: '#74b9ff'
						}}>
							{gameState.countdown === 0 ? 'GO!' : gameState.countdown}
						</div>
					)}
				</div>

				{/* Game Controls */}
				<div style={{ marginTop: 30, display: 'flex', gap: 20, flexWrap: 'wrap', justifyContent: 'center' }}>
					{!gameState?.armed && !gameState?.game_started && (
						<button
							onClick={startGame}
							style={{
								padding: '15px 40px',
								border: 'none',
								borderRadius: 25,
								background: 'linear-gradient(45deg, #00b894, #00a085)',
								color: 'white',
								fontSize: 18,
								fontWeight: 'bold',
								cursor: 'pointer',
								boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
							}}
						>
							🎯 Start Round {(gameState?.game_status?.round || 0) + 1}
						</button>
					)}
					
					<button
						onClick={() => setCurrentPage('difficulty')}
						style={{
							padding: '10px 20px',
							border: '2px solid #74b9ff',
							borderRadius: 20,
							background: 'transparent',
							color: '#74b9ff',
							cursor: 'pointer'
						}}
					>
						⚙️ Settings
					</button>
				</div>

				{/* Round Result Display */}
				{gameState?.game_started && gameState?.user_choice && (
					<div style={{
						marginTop: 30,
						padding: 25,
						background: 'rgba(255,255,255,0.1)',
						borderRadius: 15,
						textAlign: 'center',
						backdropFilter: 'blur(10px)'
					}}>
						<div style={{ fontSize: 20, marginBottom: 15 }}>Round Result</div>
						<div style={{ display: 'flex', justifyContent: 'center', gap: 40, marginBottom: 15 }}>
							<div>
								<div style={{ fontSize: 48 }}>{getGestureEmoji(gameState.user_choice)}</div>
								<div>You</div>
							</div>
							<div style={{ display: 'flex', alignItems: 'center', fontSize: 24 }}>VS</div>
							<div>
								<div style={{ fontSize: 48 }}>{getGestureEmoji(gameState.computer_choice)}</div>
								<div>AI</div>
							</div>
						</div>
						<div style={{ fontSize: 18, fontWeight: 'bold', color: getWinnerColor(gameState.winner) }}>
							{gameState.winner}
						</div>
					</div>
				)}
			</div>
		</div>
	)

	const ResultsPage = () => (
		<div style={{
			display: 'flex',
			flexDirection: 'column',
			alignItems: 'center',
			justifyContent: 'center',
			minHeight: '100vh',
			background: gameState?.game_status?.game_winner?.includes('Player') ? 
				'linear-gradient(135deg, #00b894 0%, #00a085 100%)' : 
				'linear-gradient(135deg, #e17055 0%, #d63031 100%)',
			color: 'white',
			textAlign: 'center',
			padding: 20
		}}>
			<div style={{
				background: 'rgba(255,255,255,0.1)',
				borderRadius: 20,
				padding: 40,
				backdropFilter: 'blur(10px)',
				border: '1px solid rgba(255,255,255,0.2)',
				maxWidth: 600
			}}>
				{/* Final Result */}
				<div style={{ fontSize: 60, marginBottom: 20 }}>
					{gameState?.game_status?.game_winner?.includes('Player') ? '🏆' : '🤖'}
				</div>
				<h1 style={{ fontSize: 36, marginBottom: 20 }}>
					{gameState?.game_status?.game_winner}
				</h1>

				{/* Final Score */}
				<div style={{ display: 'flex', justifyContent: 'center', gap: 40, marginBottom: 30 }}>
					<div style={{ textAlign: 'center' }}>
						<div style={{ fontSize: 48, fontWeight: 'bold' }}>
							{gameState?.game_status?.player_score}
						</div>
						<div style={{ fontSize: 16 }}>Your Score</div>
					</div>
					<div style={{ fontSize: 24, display: 'flex', alignItems: 'center' }}>-</div>
					<div style={{ textAlign: 'center' }}>
						<div style={{ fontSize: 48, fontWeight: 'bold' }}>
							{gameState?.game_status?.computer_score}
						</div>
						<div style={{ fontSize: 16 }}>AI Score</div>
					</div>
				</div>

				{/* Round History */}
				{gameState?.game_status?.round_history && (
					<div style={{ marginBottom: 30 }}>
						<h3 style={{ marginBottom: 15 }}>Round by Round</h3>
						{gameState.game_status.round_history.map((round, index) => (
							<div key={index} style={{
								display: 'flex',
								justifyContent: 'space-between',
								alignItems: 'center',
								padding: '10px 20px',
								marginBottom: 10,
								background: 'rgba(255,255,255,0.1)',
								borderRadius: 10
							}}>
								<span>Round {round.round}</span>
								<span>{getGestureEmoji(round.user_choice)} vs {getGestureEmoji(round.computer_choice)}</span>
								<span style={{ 
									color: round.result === 'player' ? '#00b894' : 
										   round.result === 'computer' ? '#e17055' : '#fdcb6e'
								}}>
									{round.result === 'player' ? 'Win' : round.result === 'computer' ? 'Loss' : 'Draw'}
								</span>
							</div>
						))}
					</div>
				)}

				{/* Action Buttons */}
				<div style={{ display: 'flex', gap: 20, justifyContent: 'center' }}>
					<button
						onClick={resetGame}
						style={{
							padding: '15px 30px',
							border: 'none',
							borderRadius: 25,
							background: 'rgba(255,255,255,0.2)',
							color: 'white',
							cursor: 'pointer',
							fontSize: 16,
							fontWeight: 'bold'
						}}
					>
						🏠 Main Menu
					</button>
					<button
						onClick={() => {
							resetGame()
							setTimeout(() => setCurrentPage('difficulty'), 100)
						}}
						style={{
							padding: '15px 30px',
							border: 'none',
							borderRadius: 25,
							background: 'linear-gradient(45deg, #74b9ff, #0984e3)',
							color: 'white',
							cursor: 'pointer',
							fontSize: 16,
							fontWeight: 'bold'
						}}
					>
						🔄 Play Again
					</button>
				</div>
			</div>
		</div>
	)

	// Helper functions
	const getGestureEmoji = (gesture) => {
		const emojis = { 'Rock': '✊', 'Paper': '✋', 'Scissors': '✌️' }
		return emojis[gesture] || '❓'
	}

	const getWinnerColor = (winner) => {
		if (winner?.includes('You Win')) return '#00b894'
		if (winner?.includes('Computer')) return '#e17055'
		return '#fdcb6e'
	}

	// Render current page
	const pages = {
		welcome: <WelcomePage />,
		difficulty: <DifficultyPage />,
		gameplay: <GameplayPage />,
		results: <ResultsPage />
	}

	return (
		<div style={{ fontFamily: 'Arial, sans-serif' }}>
			{pages[currentPage] || <WelcomePage />}
			
			{error && (
				<div style={{
					position: 'fixed',
					bottom: 20,
					right: 20,
					background: '#e17055',
					color: 'white',
					padding: 15,
					borderRadius: 10,
					boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
				}}>
					{error}
				</div>
			)}
		</div>
	)
}