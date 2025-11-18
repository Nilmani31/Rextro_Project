# utils.py
import random

class GameManager:
    def __init__(self):
        self.current_level = "Easy"  # Easy, Medium, Hard
        self.round_count = 0
        self.max_rounds = 3
        self.player_score = 0
        self.computer_score = 0
        self.round_history = []
        self.game_completed = False
        
        # Difficulty settings
        self.difficulty_settings = {
            "Easy": {
                "choices": ["Rock", "Paper", "Scissors"],
                "weights": [1, 1, 1],  # Equal probability
                "strategy": "random"
            },
            "Medium": {
                "choices": ["Rock", "Paper", "Scissors"],
                "weights": [1, 1, 1],
                "strategy": "adaptive"  # Learns from player patterns
            },
            "Hard": {
                "choices": ["Rock", "Paper", "Scissors"],
                "weights": [1, 1, 1],
                "strategy": "counter"  # Actively counters player
            }
        }
        
        # Track player patterns for adaptive AI
        self.player_history = []
        self.player_patterns = {"Rock": 0, "Paper": 0, "Scissors": 0}
    
    def set_difficulty(self, level):
        """Set game difficulty level"""
        if level in ["Easy", "Medium", "Hard"]:
            self.current_level = level
            return True
        return False
    
    def get_computer_choice(self):
        """Get computer choice based on difficulty level"""
        settings = self.difficulty_settings[self.current_level]
        strategy = settings["strategy"]
        
        if strategy == "random":
            return random.choice(settings["choices"])
        
        elif strategy == "adaptive":
            return self._get_adaptive_choice()
        
        elif strategy == "counter":
            return self._get_counter_choice()
        
        return random.choice(settings["choices"])
    
    def _get_adaptive_choice(self):
        """Medium difficulty: Adapts to player patterns"""
        if len(self.player_history) < 2:
            return random.choice(["Rock", "Paper", "Scissors"])
        
        # Analyze recent player choices
        recent_choices = self.player_history[-3:] if len(self.player_history) >= 3 else self.player_history
        
        # Find most common recent choice
        choice_counts = {}
        for choice in recent_choices:
            choice_counts[choice] = choice_counts.get(choice, 0) + 1
        
        if choice_counts:
            most_common = max(choice_counts, key=choice_counts.get)
            # 60% chance to counter the most common choice, 40% random
            if random.random() < 0.6:
                return self._get_counter_to(most_common)
        
        return random.choice(["Rock", "Paper", "Scissors"])
    
    def _get_counter_choice(self):
        """Hard difficulty: Actively counters player"""
        if len(self.player_history) == 0:
            return random.choice(["Rock", "Paper", "Scissors"])
        
        # Predict player's next move based on patterns
        predicted_move = self._predict_player_move()
        
        # 80% chance to counter prediction, 20% random
        if random.random() < 0.8:
            return self._get_counter_to(predicted_move)
        
        return random.choice(["Rock", "Paper", "Scissors"])
    
    def _predict_player_move(self):
        """Predict player's next move based on history"""
        if len(self.player_history) < 2:
            return random.choice(["Rock", "Paper", "Scissors"])
        
        # Look for patterns in last few moves
        last_move = self.player_history[-1]
        
        # Simple pattern: if player repeated last move, they might repeat again
        if len(self.player_history) >= 2 and self.player_history[-1] == self.player_history[-2]:
            return last_move
        
        # Frequency-based prediction
        total_moves = len(self.player_history)
        rock_freq = self.player_patterns["Rock"] / total_moves
        paper_freq = self.player_patterns["Paper"] / total_moves
        scissors_freq = self.player_patterns["Scissors"] / total_moves
        
        # Return most frequent choice
        frequencies = {"Rock": rock_freq, "Paper": paper_freq, "Scissors": scissors_freq}
        return max(frequencies, key=frequencies.get)
    
    def _get_counter_to(self, choice):
        """Get the choice that beats the given choice"""
        counters = {
            "Rock": "Paper",
            "Paper": "Scissors", 
            "Scissors": "Rock"
        }
        return counters.get(choice, "Rock")
    
    def play_round(self, user_choice, computer_choice):
        """Play a single round and update scores"""
        if self.game_completed:
            return None
        
        # Add to player history and patterns
        if user_choice:
            self.player_history.append(user_choice)
            self.player_patterns[user_choice] = self.player_patterns.get(user_choice, 0) + 1
        
        # Determine round winner
        round_result = self._get_round_winner(user_choice, computer_choice)
        
        # Update scores
        if round_result == "player":
            self.player_score += 1
        elif round_result == "computer":
            self.computer_score += 1
        
        # Store round history
        round_info = {
            "round": self.round_count + 1,
            "user_choice": user_choice,
            "computer_choice": computer_choice,
            "result": round_result,
            "score": f"{self.player_score}-{self.computer_score}"
        }
        self.round_history.append(round_info)
        
        # Increment round
        self.round_count += 1
        
        # Check if game is completed
        if self.round_count >= self.max_rounds:
            self.game_completed = True
        
        return round_info
    
    def _get_round_winner(self, user, computer):
        """Determine winner of a single round"""
        if user == computer:
            return "draw"
        elif (user == "Rock" and computer == "Scissors") or \
             (user == "Paper" and computer == "Rock") or \
             (user == "Scissors" and computer == "Paper"):
            return "player"
        else:
            return "computer"
    
    def get_game_winner(self):
        """Get overall game winner after all rounds"""
        if not self.game_completed:
            return None
        
        if self.player_score > self.computer_score:
            return "Player Wins the Game!"
        elif self.computer_score > self.player_score:
            return "Computer Wins the Game!"
        else:
            return "Game is a Tie!"
    
    def get_game_status(self):
        """Get current game status"""
        return {
            "level": self.current_level,
            "round": self.round_count,
            "max_rounds": self.max_rounds,
            "player_score": self.player_score,
            "computer_score": self.computer_score,
            "game_completed": self.game_completed,
            "game_winner": self.get_game_winner() if self.game_completed else None,
            "round_history": self.round_history
        }
    
    def reset_game(self):
        """Reset game for new session"""
        self.round_count = 0
        self.player_score = 0
        self.computer_score = 0
        self.round_history = []
        self.game_completed = False
        self.player_history = []
        self.player_patterns = {"Rock": 0, "Paper": 0, "Scissors": 0}

# Legacy functions for backward compatibility
def get_computer_choice():
    return random.choice(["Rock", "Paper", "Scissors"])

def get_winner(user, computer):
    if user == computer:
        return "Draw"
    elif (user == "Rock" and computer == "Scissors") or \
         (user == "Paper" and computer == "Rock") or \
         (user == "Scissors" and computer == "Paper"):
        return "You Win!"
    else:
        return "Computer Wins!"
