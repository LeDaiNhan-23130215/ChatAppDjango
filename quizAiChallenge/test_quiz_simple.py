"""
Quick Test Script - Simple version for Django shell
====================================================

Usage in Django shell:
python manage.py shell
>>> exec(open('test_quiz_simple.py').read())
"""

from django.conf import settings
from django.contrib.auth import get_user_model
import requests
import json
import time

User = get_user_model()

print("\n" + "="*70)
print("🚀 AI QUIZ GENERATION - SIMPLE TEST")
print("="*70)

# 1️⃣ Create/Get User
print("\n1️⃣ STEP: Create/Get User")
user, created = User.objects.get_or_create(
    username="nhan_test_shell_026",
    defaults={
        "declared_level": "Advanced",
        "goals": "job",
        "profession": "engineer",
        "motivation_level": 9,
    }
)
print(f"   User: {user.username} (ID: {user.id}) - {'NEW' if created else 'EXISTING'}")

# 2️⃣ Prepare Payload
print("\n2️⃣ STEP: Prepare Payload")
payload = {
    "user_id": user.id,
    "quiz_size": 3,  # Start small for testing
    "declared_level": "Advanced",
    "profession": "software engineer",
    "preferred_topics": [
        "cloud computing",
        "API design",
        "debugging",
    ],
    "weak_skills": [
        "gerunds vs infinitives",
        "prepositions in technical contexts",
    ],
    "extra_instructions": "Focus on IT workplace scenarios.",
}

print(f"   User ID: {payload['user_id']}")
print(f"   Quiz Size: {payload['quiz_size']}")
print(f"   Topics: {len(payload['preferred_topics'])}")
print(f"   Weak Skills: {len(payload['weak_skills'])}")

# 3️⃣ Send Request
print("\n3️⃣ STEP: Send Request to /api/ai/generate/")
headers = {
    "Content-Type": "application/json",
    "X-AI-Worker-Token": settings.AI_WORKER_TOKEN,
}

try:
    response = requests.post(
        "http://localhost:8000/api/ai/generate/",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"   Status Code: {response.status_code}")
    data = response.json()
    print(f"   Response:")
    print(f"      Status: {data.get('status')}")
    print(f"      Task ID: {data.get('task_id')}")
    print(f"      Message: {data.get('message')}")
    
    task_id = data.get("task_id")
    
    if response.status_code == 202:
        print(f"\n✅ SUCCESS! Task created.")
        
        # 4️⃣ Check in Database
        print(f"\n4️⃣ STEP: Check QuizTask in Database")
        from question_generator.models import QuizTask
        
        task = QuizTask.objects.get(task_id=task_id)
        print(f"   Task ID: {task.task_id}")
        print(f"   Status: {task.status}")
        print(f"   User: {task.user.username}")
        print(f"   Quiz Size: {task.quiz_size}")
        print(f"   Created: {task.created_at}")
        
        # 5️⃣ Check Status Endpoint
        print(f"\n5️⃣ STEP: Check Status Endpoint (/api/ai/tasks/{task_id}/)")
        status_response = requests.get(
            f"http://localhost:8000/api/ai/tasks/{task_id}/",
            timeout=10
        )
        status_data = status_response.json()
        print(f"   API Status Code: {status_response.status_code}")
        print(f"   Status: {status_data.get('status')}")
        print(f"   Questions Created: {status_data.get('questions_created')}")
        
        # 6️⃣ Instructions
        print(f"\n6️⃣ WHAT TO DO NEXT:")
        print(f"   ⏳ AI Worker is processing (takes 3-10 minutes)")
        print(f"   📍 Check status: http://localhost:8000/api/ai/tasks/{task_id}/")
        print(f"   📊 View in admin: http://localhost:8000/admin/question_generator/quiztask/")
        print(f"   🔍 Questions will appear in: http://localhost:8000/admin/quiz/question/")
        
    else:
        print(f"\n❌ Error: {data.get('error')}")
        
except Exception as e:
    print(f"\n❌ Request failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✨ Test Complete! Check status after 1-2 minutes.")
print("="*70)
