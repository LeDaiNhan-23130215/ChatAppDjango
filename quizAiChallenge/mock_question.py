import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')
django.setup()

from quiz_ai_battle.models import Question

# Xóa dữ liệu cũ
Question.objects.all().delete()

questions_data = [
    {
        "content": "What is the capital of France?",
        "option_a": "Berlin",
        "option_b": "Madrid",
        "option_c": "Paris",
        "option_d": "Rome",
        "correct_answer": "C",
    },
    {
        "content": "Which planet is known as the Red Planet?",
        "option_a": "Earth",
        "option_b": "Mars",
        "option_c": "Jupiter",
        "option_d": "Venus",
        "correct_answer": "B",
    },
    {
        "content": "Which language is primarily spoken in Brazil?",
        "option_a": "Spanish",
        "option_b": "Portuguese",
        "option_c": "French",
        "option_d": "English",
        "correct_answer": "B",
    },
    {
        "content": "What is 5 + 7?",
        "option_a": "10",
        "option_b": "11",
        "option_c": "12",
        "option_d": "13",
        "correct_answer": "C",
    },
    {
        "content": "Which ocean is the largest?",
        "option_a": "Atlantic Ocean",
        "option_b": "Indian Ocean",
        "option_c": "Pacific Ocean",
        "option_d": "Arctic Ocean",
        "correct_answer": "C",
    },
    {
        "content": "Who wrote 'Romeo and Juliet'?",
        "option_a": "Charles Dickens",
        "option_b": "William Shakespeare",
        "option_c": "Jane Austen",
        "option_d": "Mark Twain",
        "correct_answer": "B",
    },
    {
        "content": "Which gas do humans need to breathe?",
        "option_a": "Carbon Dioxide",
        "option_b": "Oxygen",
        "option_c": "Nitrogen",
        "option_d": "Hydrogen",
        "correct_answer": "B",
    },
    {
        "content": "Which continent is Egypt located in?",
        "option_a": "Asia",
        "option_b": "Europe",
        "option_c": "Africa",
        "option_d": "South America",
        "correct_answer": "C",
    },
    {
        "content": "What is the boiling point of water at sea level?",
        "option_a": "90°C",
        "option_b": "95°C",
        "option_c": "100°C",
        "option_d": "110°C",
        "correct_answer": "C",
    },
    {
        "content": "Which instrument has keys, pedals, and strings?",
        "option_a": "Guitar",
        "option_b": "Piano",
        "option_c": "Violin",
        "option_d": "Drums",
        "correct_answer": "B",
    },
]

# Thêm dữ liệu vào database
for q in questions_data:
    question = Question.objects.create(**q)
    print(f"✅ Added Question {question.id}: {q['content'][:50]}...")

print(f"\n📊 Total questions: {Question.objects.count()}")
