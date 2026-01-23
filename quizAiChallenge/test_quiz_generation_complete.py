"""
Test Script - AI Quiz Generation Complete Flow
==============================================

Hướng dẫn sử dụng:
1. python manage.py shell
2. exec(open('test_quiz_generation_complete.py').read())

Hoặc chạy trực tiếp:
python test_quiz_generation_complete.py

Flow:
1. Tạo user test
2. POST request tới Django: /api/ai/generate/
3. Django trả lại task_id (status=202)
4. AI worker xử lý trong background (3-10 phút)
5. Check task status qua /api/ai/tasks/<task_id>/
"""

import os
import sys
import django
import requests
import json
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from question_generator.models import QuizTask

User = get_user_model()

# ============================================================================
# CONFIG
# ============================================================================

BASE_URL = "http://localhost:8000"  # Change to ngrok URL if needed
API_ENDPOINT = f"{BASE_URL}/api/ai"

# User data
TEST_USERNAME = "nhan_test_shell_026"
TEST_PASSWORD = "test123456"

# AI Worker token
AI_WORKER_TOKEN = settings.AI_WORKER_TOKEN

# ============================================================================
# STEP 1: Create/Get User
# ============================================================================

print("\n" + "="*80)
print("STEP 1: CREATE/GET TEST USER")
print("="*80)

user, created = User.objects.get_or_create(
    username=TEST_USERNAME,
    defaults={
        "first_name": "Nhan",
        "last_name": "Test",
        "email": f"{TEST_USERNAME}@test.com",
        "declared_level": "Advanced",
        "goals": "job",
        "profession": "engineer",
        "motivation_level": 9,
    }
)

if created:
    print(f"✅ Created new user: {user.username} (ID: {user.id})")
else:
    print(f"✅ Using existing user: {user.username} (ID: {user.id})")

print(f"   Email: {user.email}")
print(f"   Level: {user.declared_level}")
print(f"   Profession: {user.profession}")

# ============================================================================
# STEP 2: Send Request to Django (POST /api/ai/generate/)
# ============================================================================

print("\n" + "="*80)
print("STEP 2: SEND REQUEST TO DJANGO (/api/ai/generate/)")
print("="*80)

payload = {
    "user_id": user.id,  # ⭐ Use user.id
    "quiz_size": 5,  # Start with 5 for quick testing (can be 1-11)
    "declared_level": "Advanced",
    "goals": "job",
    "profession": "software engineer",
    "referred_frequency": "daily",
    "study_frequency": "daily",
    "motivation_level": 9,
    "hobby": "competitive programming, reading tech blogs",
    
    # 🎯 Topics & Skills
    "preferred_topics": [
        "cloud computing",
        "API design and integration",
        "debugging and error handling",
        "agile and scrum methodologies",
        "system security and best practices",
        "databases and SQL optimization"
    ],
    "weak_skills": [
        "subjunctive mood in formal requests",
        "gerunds vs infinitives",
        "prepositions in technical contexts",
        "past perfect tense in bug reporting"
    ],
    
    # 📝 Extra instructions
    "extra_instructions": (
        "Focus on realistic workplace scenarios for a software engineer in a Vietnamese tech company. "
        "Prioritize questions about code review, sprint retrospectives, cloud migration, API integration. "
        "Avoid basic questions. Keep advanced level and IT/CS focused."
    )
}

headers = {
    "Content-Type": "application/json",
    "X-AI-Worker-Token": AI_WORKER_TOKEN
}

print(f"\n📤 URL: {API_ENDPOINT}/generate/")
print(f"\n📋 Payload (truncated):")
print(f"   user_id: {payload['user_id']}")
print(f"   quiz_size: {payload['quiz_size']}")
print(f"   declared_level: {payload['declared_level']}")
print(f"   preferred_topics: {len(payload['preferred_topics'])} topics")
print(f"   weak_skills: {len(payload['weak_skills'])} skills")

try:
    print(f"\n⏳ Sending request to Django...")
    response = requests.post(
        f"{API_ENDPOINT}/generate/",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    print(f"✅ Response Status: {response.status_code}")
    
    data = response.json()
    print(f"\n📥 Response:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if response.status_code == 202:
        task_id = data.get("task_id")
        print(f"\n✨ SUCCESS! Task Created")
        print(f"   Task ID: {task_id}")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
    else:
        print(f"\n❌ Error: {data.get('error', 'Unknown error')}")
        exit(1)
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
    exit(1)

# ============================================================================
# STEP 3: Check Task Status in Database
# ============================================================================

print("\n" + "="*80)
print("STEP 3: CHECK TASK STATUS IN DATABASE")
print("="*80)

try:
    quiz_task = QuizTask.objects.get(task_id=task_id)
    print(f"\n✅ QuizTask found in database:")
    print(f"   Task ID: {quiz_task.task_id}")
    print(f"   User: {quiz_task.user.username} (ID: {quiz_task.user.id})")
    print(f"   Status: {quiz_task.status}")
    print(f"   Quiz Size: {quiz_task.quiz_size}")
    print(f"   Created At: {quiz_task.created_at}")
    print(f"   Questions Created: {quiz_task.questions_created}")
except QuizTask.DoesNotExist:
    print(f"❌ Task not found in database!")
    exit(1)

# ============================================================================
# STEP 4: Poll Status Endpoint
# ============================================================================

print("\n" + "="*80)
print("STEP 4: POLLING TASK STATUS (/api/ai/tasks/<task_id>/)")
print("="*80)

print(f"\n📌 Note: AI Worker takes 3-10 minutes to process")
print(f"   This script will poll status every 30 seconds (max 10 times)")
print(f"\n   You can also check manually:")
print(f"   - URL: {API_ENDPOINT}/tasks/{task_id}/")
print(f"   - Or: {BASE_URL}/admin/question_generator/quiztask/")

POLL_INTERVAL = 30  # seconds
MAX_POLLS = 10

for poll_count in range(MAX_POLLS):
    try:
        response = requests.get(
            f"{API_ENDPOINT}/tasks/{task_id}/",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            questions_created = data.get("questions_created", 0)
            duration = data.get("duration_seconds")
            
            print(f"\n[Poll #{poll_count + 1}] {datetime.now().strftime('%H:%M:%S')}")
            print(f"   Status: {status}")
            print(f"   Questions: {questions_created}/{data.get('quiz_size_requested')}")
            
            if status == "completed":
                print(f"\n✅ TASK COMPLETED!")
                print(f"   Duration: {duration} seconds ({duration/60:.1f} minutes)")
                print(f"   Questions Created: {questions_created}")
                print(f"   Completed At: {data.get('completed_at')}")
                break
            elif status == "failed":
                print(f"\n❌ TASK FAILED!")
                print(f"   Error: {data.get('error_message')}")
                break
            elif status == "queued":
                print(f"   Waiting for AI worker to start processing...")
            elif status == "processing":
                print(f"   AI worker is processing...")
            
        else:
            print(f"   ❌ Error: {response.status_code}")
            break
            
    except Exception as e:
        print(f"   ❌ Poll failed: {str(e)}")
        break
    
    if poll_count < MAX_POLLS - 1:
        print(f"   ⏳ Next poll in {POLL_INTERVAL} seconds... (Ctrl+C to stop)")
        time.sleep(POLL_INTERVAL)

# ============================================================================
# STEP 5: Database Info
# ============================================================================

print("\n" + "="*80)
print("STEP 5: DATABASE SUMMARY")
print("="*80)

from django.db.models import Count
from quiz.models import Question

# Count tasks
total_tasks = QuizTask.objects.count()
completed_tasks = QuizTask.objects.filter(status='completed').count()
failed_tasks = QuizTask.objects.filter(status='failed').count()
pending_tasks = QuizTask.objects.filter(status__in=['queued', 'processing']).count()

print(f"\n📊 QuizTask Statistics:")
print(f"   Total Tasks: {total_tasks}")
print(f"   Completed: {completed_tasks}")
print(f"   Failed: {failed_tasks}")
print(f"   Pending: {pending_tasks}")

# Count questions
total_questions = Question.objects.count()
print(f"\n📊 Question Statistics:")
print(f"   Total Questions: {total_questions}")

# Latest tasks
print(f"\n📊 Latest 3 Tasks:")
for t in QuizTask.objects.order_by('-created_at')[:3]:
    print(f"   - {t.task_id[:12]}... | {t.status:10} | {t.questions_created} questions")

# ============================================================================
# FINAL INSTRUCTIONS
# ============================================================================

print("\n" + "="*80)
print("📝 WHAT TO DO NEXT")
print("="*80)

print(f"""
1. ✅ Request created successfully
   - Task ID: {task_id}
   - Status: {quiz_task.status}

2. ⏳ AI Worker is processing in background (3-10 minutes)
   - Check logs on Colab/AI Worker server
   - Monitor task status at: {API_ENDPOINT}/tasks/{task_id}/

3. 🎯 When completed:
   - Questions will be saved to database
   - Task status will change to 'completed'
   - Visit: {BASE_URL}/admin/quiz/question/
   - To see generated questions

4. 🔍 Manual checks:
   - Admin: {BASE_URL}/admin/question_generator/quiztask/
   - Current task: {BASE_URL}/admin/question_generator/quiztask/{quiz_task.id}/change/
   
5. 📊 Debug commands:
   python manage.py shell
   >>> from question_generator.models import QuizTask
   >>> task = QuizTask.objects.get(task_id='{task_id}')
   >>> task.status
   >>> task.questions_created
   >>> from quiz.models import Question
   >>> Question.objects.count()

6. 🧪 Test the endpoints:
   
   # Check task status
   curl {API_ENDPOINT}/tasks/{task_id}/
   
   # List all user tasks
   curl "{API_ENDPOINT}/tasks/?user_id={user.id}"
   
   # Check specific status
   curl "{API_ENDPOINT}/tasks/?status=completed"
""")

print("="*80)
print("✨ Test Complete!")
print("="*80)
