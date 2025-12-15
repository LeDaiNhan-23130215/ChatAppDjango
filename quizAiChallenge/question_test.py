from quiz_ai_battle.models import Question

Question.objects.all().delete()

questions_data = [
    {
        "content": "What is the capital of France?",
        "option_a": "London",
        "option_b": "Paris",
        "option_c": "Berlin",
        "option_d": "Madrid",
        "correct_answer": "B",
    },
    {
        "content": "What is 2 + 2?",
        "option_a": "3",
        "option_b": "4",
        "option_c": "5",
        "option_d": "6",
        "correct_answer": "B",
    },
]

for q in questions_data:
    Question.objects.create(**q)
    print("Added:", q["content"])

print("Total:", Question.objects.count())
