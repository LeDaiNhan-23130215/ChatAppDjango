import os
from groq import Groq
from .BaseAI import BaseAI

class GPTAI(BaseAI):
    def __init__(self, difficulty="medium"):
        self.difficulty = difficulty

    def get_answer(self, question):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY not loaded")

        client = Groq(api_key=api_key)

        # Map độ khó -> temperature
        difficulty_map = {
            "easy": 1.0,      # nhiều ngẫu nhiên, dễ sai
            "medium": 0.7,    # cân bằng
            "hard": 0.3,      # ít ngẫu nhiên, chính xác hơn
            "expert": 0.0,    # gần như luôn đúng
        }
        temperature = difficulty_map.get(self.difficulty, 0.7)

        prompt = f"""
You are a quiz AI.
Choose the correct answer.

Question:
{question.content}

A. {question.option_a}
B. {question.option_b}
C. {question.option_c}
D. {question.option_d}

Respond with ONLY one letter: A, B, C, or D.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a smart quiz player."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )

        answer = response.choices[0].message.content.strip().upper()

        if answer not in ["A", "B", "C", "D"]:
            return "A"

        return answer
