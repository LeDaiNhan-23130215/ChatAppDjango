import os
from openai import OpenAI
from .BaseAI import BaseAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class GPTAI(BaseAI):
    def get_answer(self, question):
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
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are smart quiz player."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        answer = response.choices[0].message.content.strip().upper()

        if answer not in ["A", "B", "C", "D"]:
            return "A"
        return answer