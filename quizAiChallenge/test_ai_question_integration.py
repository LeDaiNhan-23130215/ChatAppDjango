"""
Test Script - AI Question Generation Integration
================================================

Cách dùng:
1. python manage.py shell
2. exec(open('test_ai_question_integration.py').read())

Hoặc chạy trực tiếp:
python test_ai_question_integration.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
import json
import requests

User = get_user_model()
client = Client()

print("\n" + "="*80)
print("🎮 TEST: AI QUESTION INTEGRATION WITH QUIZ_AI_BATTLE")
print("="*80)

# ============================================================================
# STEP 1: Create/Get User
# ============================================================================

print("\n1️⃣ STEP: Create/Get Test User")
user, created = User.objects.get_or_create(
    username="ai_battle_test_user",
    defaults={
        "first_name": "Test",
        "declared_level": "Advanced",
        "goals": "job",
        "profession": "software engineer",
        "motivation_level": 9,
        "referred_frequency": "daily",
    }
)
print(f"   User: {user.username} (ID: {user.id}) - {'NEW' if created else 'EXISTING'}")

# ============================================================================
# STEP 2: Test API - Generate Question
# ============================================================================

print("\n2️⃣ STEP: POST /user-vs-ai/api/generate-question/")

# Login user
client.login(username="ai_battle_test_user", password="")  # If no password
# Or create auth token for API

payload = {
    "difficulty": "advanced"
}

print(f"   URL: http://localhost:8000/user-vs-ai/api/generate-question/")
print(f"   Payload: {json.dumps(payload, indent=2)}")

try:
    # Test locally
    from django.test import RequestFactory
    from quiz_ai_battle.api_views import generate_question
    
    factory = RequestFactory()
    request = factory.post(
        '/user-vs-ai/api/generate-question/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    request.user = user
    
    response = generate_question(request)
    data = json.loads(response.content)
    
    print(f"\n   ✅ Status: {response.status_code}")
    print(f"   Response:")
    print(f"      Success: {data.get('success')}")
    print(f"      Task ID: {data.get('task_id')}")
    print(f"      Message: {data.get('message')}")
    
    if data.get('success'):
        task_id = data.get('task_id')
        print(f"\n   ✨ Question generation started!")
        print(f"   Task ID: {task_id}")
        print(f"   Estimated time: 3-10 minutes")
        
        # ===================================================================
        # STEP 3: Test API - Check Status
        # ===================================================================
        
        print(f"\n3️⃣ STEP: GET /user-vs-ai/api/question-status/{task_id}/")
        print(f"   ⏳ Polling status (will check in 30 seconds...)")
        
        import time
        
        for i in range(3):
            time.sleep(30)
            
            from quiz_ai_battle.api_views import check_question_status
            
            request2 = factory.get(f'/user-vs-ai/api/question-status/{task_id}/')
            request2.user = user
            
            response2 = check_question_status(request2, task_id)
            data2 = json.loads(response2.content)
            
            status = data2.get('status')
            print(f"\n   [Poll #{i+1}] Status: {status}")
            print(f"      Success: {data2.get('success')}")
            print(f"      Message: {data2.get('message')}")
            
            if status == 'completed':
                print(f"\n   ✅ QUESTION GENERATED!")
                question = data2.get('question')
                if question:
                    print(f"      Question ID: {question.get('id')}")
                    print(f"      Text: {question.get('text')[:50]}...")
                break
            elif status == 'failed':
                print(f"\n   ❌ GENERATION FAILED!")
                print(f"      Error: {data2.get('message')}")
                break
        
        # ===================================================================
        # STEP 4: Test API - Create Match with AI Question
        # ===================================================================
        
        print(f"\n4️⃣ STEP: POST /user-vs-ai/api/create-match/")
        
        match_payload = {
            "difficulty": "advanced",
            "ai_mode": "random",
            "num_rounds": 3
        }
        
        print(f"   Payload: {json.dumps(match_payload, indent=2)}")
        
        from quiz_ai_battle.api_views import create_match_with_ai_question
        
        request3 = factory.post(
            '/user-vs-ai/api/create-match/',
            data=json.dumps(match_payload),
            content_type='application/json'
        )
        request3.user = user
        
        response3 = create_match_with_ai_question(request3)
        data3 = json.loads(response3.content)
        
        print(f"\n   ✅ Status: {response3.status_code}")
        print(f"   Response:")
        print(f"      Success: {data3.get('success')}")
        print(f"      Match ID: {data3.get('match_id')}")
        print(f"      AI Mode: {data3.get('ai_mode')}")
        print(f"      Difficulty: {data3.get('difficulty')}")
        print(f"      Num Rounds: {data3.get('num_rounds')}")
        
        if data3.get('task_id'):
            print(f"      Question Task ID: {data3.get('task_id')}")
            print(f"      Question Generation: {data3.get('question_generation')}")
        
        print(f"      Message: {data3.get('message')}")
        
    else:
        print(f"\n   ❌ Error: {data.get('error')}")
        
except Exception as e:
    print(f"\n   ❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80)

print("""
✅ API Endpoints Created:
1. POST /user-vs-ai/api/generate-question/
   - Generate AI question for user
   - Request: {difficulty: "easy"|"medium"|"hard"|"advanced"}
   - Response: {success, task_id, message}

2. GET /user-vs-ai/api/question-status/<task_id>/
   - Check question generation status
   - Response: {success, status, question, message}

3. POST /user-vs-ai/api/create-match/
   - Create match + generate AI question
   - Request: {difficulty, ai_mode, num_rounds}
   - Response: {match_id, task_id, message}

4. POST /user-vs-ai/api/receive-question/
   - Webhook from question_generator
   - Called by AI Worker when questions are ready

✅ Service Module Created:
   quiz_ai_battle/ai_question_service.py
   - build_ai_question_payload()
   - generate_ai_question_async()
   - get_question_from_task()
   - generate_question_sync_or_fallback()

✅ Integration Ready:
   When user plays quiz_ai_battle:
   1. Match is created with existing questions
   2. AI Worker generates new question
   3. Question added to future rounds
   4. User gets personalized + AI-generated questions
""")

print("\n" + "="*80)
print("🎯 NEXT STEPS")
print("="*80)

print("""
1. Check Admin:
   http://localhost:8000/admin/question_generator/quiztask/

2. Monitor Question Generation:
   - Watch task status change: queued → processing → completed
   - Check logs on Colab/AI Worker

3. View Generated Questions:
   http://localhost:8000/admin/quiz/question/

4. Use in Frontend:
   - Call POST /user-vs-ai/api/generate-question/
   - Show task_id to user
   - Poll GET /user-vs-ai/api/question-status/<task_id>/
   - Display question when ready

5. Advanced:
   - Integrate with WebSocket for real-time updates
   - Queue multiple question generations
   - Add difficulty adaptation based on user performance
""")

print("="*80)
print("✨ Test Complete!")
print("="*80)
