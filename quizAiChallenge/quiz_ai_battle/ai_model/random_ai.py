import random
from .BaseAI import BaseAI

class RandomAI(BaseAI):
    def get_answer(self, question):
        choices = [
            "A",
            "B",
            "C",
            "D"
        ]
        return random.choice(choices)