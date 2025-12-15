from .random_ai import RandomAI
from .gpt_ai import GPTAI

def get_ai(ai_mode: str):
    if ai_mode == "gpt":
        return GPTAI()
    return RandomAI()