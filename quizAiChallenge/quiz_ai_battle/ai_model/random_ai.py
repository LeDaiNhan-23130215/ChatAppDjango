import random
from .BaseAI import BaseAI

class RandomAI(BaseAI):
    def __init__(self, difficulty="medium"):
        self.difficulty = difficulty

    def get_answer(self, question):
        # Xác suất đúng theo độ khó
        difficulty_map = {
            "easy": 0.3,     # 30% đúng
            "medium": 0.6,   # 60% đúng
            "hard": 0.8,     # 80% đúng
            "expert": 0.95,  # 95% đúng
        }
        prob_correct = difficulty_map.get(self.difficulty, 0.6)

        # Quyết định đúng hay sai
        if random.random() < prob_correct:
            # Trả lời đúng
            return question.correct_answer
        else:
            # Trả lời sai ngẫu nhiên (khác đáp án đúng)
            options = ["A", "B", "C", "D"]
            options.remove(question.correct_answer)
            return random.choice(options)
