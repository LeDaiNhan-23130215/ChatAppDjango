#!/usr/bin/env python
"""
Test script to verify AI question generation integration
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from quiz_ai_battle.models import Match, Round, Question
from quiz_ai_battle.views import _trigger_ai_question_generation
from question_generator.models import QuizTask
import logging
import time

logger = logging.getLogger(__name__)

User = get_user_model()

print("\n" + "="*80)
print("TEST: AI QUESTION GENERATION INTEGRATION")
print("="*80)

# Get or create test user
user, created = User.objects.get_or_create(
    username='test_ai_integration',
    defaults={
        'email': 'test_integration@example.com',
        'first_name': 'Test',
        'declared_level': 'Intermediate',
        'goals': 'job',
        'profession': 'engineer',
    }
)
print(f"\n✅ User: {user.username} (ID: {user.id})")

# Get some questions or create them
questions = Question.objects.all()[:5]
if questions.count() < 5:
    print(f"⚠️  Only {questions.count()} questions in database")
    print("   Creating sample questions...")
    for i in range(5):
        Question.objects.create(
            text=f"Sample question {i+1}?",
            a="Option A",
            b="Option B",
            c="Option C",
            d="Option D",
            correct="A",
            difficulty="intermediate"
        )
    questions = Question.objects.all()[:5]
    print(f"✅ Created 5 sample questions")
else:
    print(f"✅ Found {questions.count()} questions in database")

# Simulate start_match
print("\n" + "-"*80)
print("STEP 1: Create a Match (simulating user starting quiz)")
print("-"*80)

match = Match.objects.create(
    user=user,
    ai_mode='random',
    ai_difficulty='medium'
)
print(f"✅ Match created: ID={match.id}")

# Create rounds with existing questions
for i, question in enumerate(questions):
    round_obj = Round.objects.create(
        match=match,
        question=question
    )
print(f"✅ Added {questions.count()} rounds to match")

# Now trigger AI question generation
print("\n" + "-"*80)
print("STEP 2: Trigger AI question generation")
print("-"*80)

try:
    print(f"Triggering AI generation for difficulty: medium")
    _trigger_ai_question_generation(user, 'medium')
    print(f"✅ Trigger called successfully")
    
    # Give background thread time to execute
    time.sleep(1)
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

# Check if QuizTask was created
print("\n" + "-"*80)
print("STEP 3: Check if AI question generation was triggered")
print("-"*80)

tasks = QuizTask.objects.filter(user=user).order_by('-created_at')[:5]
if tasks.exists():
    print(f"✅ Found {tasks.count()} tasks for user")
    for task in tasks:
        print(f"\n   Task ID: {task.task_id}")
        print(f"   Status: {task.status}")
        print(f"   Created: {task.created_at}")
        if task.status in ['completed', 'failed']:
            print(f"   Completed: {task.completed_at}")
            if task.questions_created:
                print(f"   Questions created: {task.questions_created}")
            if task.error_message:
                print(f"   Error: {task.error_message}")
else:
    print("⚠️  No tasks found - AI Worker URL may not be configured")

# Check if questions were generated
print("\n" + "-"*80)
print("STEP 4: Check Question Database")
print("-"*80)

total_questions = Question.objects.count()
print(f"✅ Total questions in database: {total_questions}")

# Get match details
print("\n" + "-"*80)
print("STEP 5: Match Details")
print("-"*80)

match_rounds = Round.objects.filter(match=match)
print(f"Match ID: {match.id}")
print(f"User: {match.user.username}")
print(f"AI Mode: {match.ai_mode}")
print(f"AI Difficulty: {match.ai_difficulty}")
print(f"Total Rounds: {match_rounds.count()}")
print(f"User Score: {match.user_score}")
print(f"AI Score: {match.ai_score}")

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

print("""
✅ What happened:

1. Created a test user with profile data
2. Created a Match (simulating user starting quiz)
3. Populated match with 5 existing questions
4. Called _trigger_ai_question_generation() function directly
5. This creates a QuizTask and forwards to AI Worker in background thread

Expected results:
- Match created successfully ✓
- QuizTask created ✓ (if AI_WORKER_URL is configured)
- AI question generation started in background

Next steps:
1. Check admin to see task progress
   http://localhost:8080/admin/question_generator/quiztask/

2. Monitor task status (queued → processing → completed)

3. When AI Worker processes, it will send results back via webhook
   Endpoint: /api/ai/receive/

4. New questions will be saved and appear in database
   http://localhost:8080/admin/quiz/question/

Configuration in settings.py:
- AI_WORKER_URL = "https://your-ngrok-url.ngrok.io"
- AI_WORKER_TOKEN = "your-token-from-colab"
""")

print("="*80)

