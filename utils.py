# utils.py
import random

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
