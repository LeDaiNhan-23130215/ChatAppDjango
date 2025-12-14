#!/usr/bin/env python
"""
Script to add 10 quiz questions to the database
Run with: python manage.py shell < add_questions.py
"""

from quiz.models import Question

questions_data = [
    {
        "text": "What is the capital of France?",
        "a": "London", "b": "Paris", "c": "Berlin", "d": "Madrid",
        "correct": "B"
    },
    {
        "text": "What is 2 + 2?",
        "a": "3", "b": "4", "c": "5", "d": "6",
        "correct": "B"
    },
    {
        "text": "What is the largest planet in our solar system?",
        "a": "Saturn", "b": "Neptune", "c": "Jupiter", "d": "Earth",
        "correct": "C"
    },
    {
        "text": "Which country is known as the 'Land of the Rising Sun'?",
        "a": "China", "b": "Japan", "c": "Thailand", "d": "South Korea",
        "correct": "B"
    },
    {
        "text": "What is the chemical symbol for Gold?",
        "a": "Go", "b": "Gd", "c": "Au", "d": "Ag",
        "correct": "C"
    },
    {
        "text": "Which ocean is the largest?",
        "a": "Atlantic", "b": "Indian", "c": "Arctic", "d": "Pacific",
        "correct": "D"
    },
    {
        "text": "Who wrote 'Romeo and Juliet'?",
        "a": "Jane Austen", "b": "William Shakespeare", "c": "Mark Twain", "d": "Charles Dickens",
        "correct": "B"
    },
    {
        "text": "What is the smallest prime number?",
        "a": "0", "b": "1", "c": "2", "d": "3",
        "correct": "C"
    },
    {
        "text": "Which country has the most population?",
        "a": "India", "b": "China", "c": "USA", "d": "Indonesia",
        "correct": "A"
    },
    {
        "text": "What year did the Titanic sink?",
        "a": "1912", "b": "1920", "c": "1905", "d": "1898",
        "correct": "A"
    }
]

# Clear existing questions
Question.objects.all().delete()
print("Cleared existing questions.")

# Add new questions
for q_data in questions_data:
    Question.objects.create(**q_data)
    print(f"Added: {q_data['text']}")

print(f"\nTotal questions in database: {Question.objects.count()}")
