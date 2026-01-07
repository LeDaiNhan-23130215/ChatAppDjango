from .random_ai import RandomAI
from .gpt_ai import GPTAI

def get_ai(ai_mode: str, ai_difficulty: str):
    if ai_mode == "gpt":
        return GPTAI(difficulty=ai_difficulty)
    return RandomAI(difficulty=ai_difficulty)
