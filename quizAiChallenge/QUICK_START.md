# 🚀 Quick Start - AI Quiz Generation

## ⚡ 5 Phút Setup

### 1. Chạy Migration
```bash
python manage.py migrate question_generator
```

### 2. Start Django Server
```bash
python manage.py runserver
```

### 3. Test bằng Django Shell

```bash
python manage.py shell
```

Dán vào shell:
```python
from django.conf import settings
from django.contrib.auth import get_user_model
import requests

User = get_user_model()

# Tạo user
user, _ = User.objects.get_or_create(
    username="test_user",
    defaults={"declared_level": "Advanced"}
)

# Request quiz
payload = {
    "user_id": user.id,
    "quiz_size": 5,
    "declared_level": "Advanced",
    "preferred_topics": ["cloud computing", "API design"],
}

response = requests.post(
    "http://localhost:8000/api/ai/generate/",
    json=payload,
    headers={"X-AI-Worker-Token": settings.AI_WORKER_TOKEN}
)

print(f"Status: {response.status_code}")
print(f"Task ID: {response.json().get('task_id')}")

# Check status mỗi 30 giây
task_id = response.json().get('task_id')
import time
for i in range(10):
    r = requests.get(f"http://localhost:8000/api/ai/tasks/{task_id}/")
    print(f"Status: {r.json()['status']}, Questions: {r.json()['questions_created']}")
    if r.json()['status'] == 'completed':
        break
    time.sleep(30)
```

---

## 📊 Kiểm Tra Kết Quả

### Admin Dashboard
```
http://localhost:8000/admin/question_generator/quiztask/
```
- Xem tất cả tasks
- Check status (queued, processing, completed, failed)
- Xem worker response

### Generated Questions
```
http://localhost:8000/admin/quiz/question/
```
- Xem các câu hỏi được tạo

### Database Query
```bash
python manage.py shell

>>> from question_generator.models import QuizTask
>>> from quiz.models import Question

# Xem tasks
>>> QuizTask.objects.filter(status='completed')
>>> QuizTask.objects.order_by('-created_at')[0]

# Xem questions
>>> Question.objects.count()
>>> Question.objects.latest('id')
```

---

## 🔄 Request Flow

```
Client
  ↓ POST /api/ai/generate/ (user_id + quiz params)
Django (1s response time)
  ↓ Validate + Create QuizTask + Forward to AI Worker
  ↓ Return 202 Accepted + task_id
  
AI Worker (runs async, 3-10 minutes)
  ↓ Process request
  ↓ Generate questions using LLM
  
AI Worker → Django
  ↓ POST /api/ai/receive/ (worker_task_id + questions)
Django (handle response)
  ↓ Validate token
  ↓ Save questions to DB
  ↓ Update QuizTask status → 'completed'
  ↓ Return 201 Created

Client (can check anytime)
  ↓ GET /api/ai/tasks/<task_id>/
Django
  ↓ Return task status + questions_created
  ↓ 200 OK
```

---

## 📝 API Endpoints

### Generate Quiz
```
POST /api/ai/generate/

Request:
{
    "user_id": 1,
    "quiz_size": 10,
    "declared_level": "Advanced",
    "profession": "engineer",
    "preferred_topics": ["cloud computing"],
    "weak_skills": ["grammar"],
    "extra_instructions": "..."
}

Response (202):
{
    "status": "queued",
    "task_id": "task-xyz-123",
    "message": "Quiz generation started..."
}
```

### Check Task Status
```
GET /api/ai/tasks/<task_id>/

Response (200):
{
    "task_id": "task-xyz-123",
    "status": "completed",  // queued, processing, completed, failed
    "user_id": 1,
    "questions_created": 10,
    "quiz_size_requested": 10,
    "created_at": "2026-01-23T10:30:00Z",
    "completed_at": "2026-01-23T10:40:00Z",
    "duration_seconds": 600,
    "error_message": ""
}
```

### List User Tasks
```
GET /api/ai/tasks/?user_id=1&status=completed&limit=10

Response (200):
{
    "count": 5,
    "limit": 10,
    "tasks": [...]
}
```

---

## ⚙️ Settings (.env)

```env
AI_WORKER_URL=https://nonelliptic-dewily-carlos.ngrok-free.dev
AI_WORKER_TOKEN=38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21
```

---

## 🧪 Test Scripts

### Simple Test (Django Shell)
```bash
python manage.py shell < test_quiz_simple.py
```

### Complete Test (Python)
```bash
python test_quiz_generation_complete.py
```

---

## 🛠️ Troubleshooting

### Task stuck at 'queued'
- Check if AI Worker is running
- Check ngrok endpoint: https://nonelliptic-dewily-carlos.ngrok-free.dev/health
- Check AI Worker logs

### Task status 'failed'
- Check `error_message` in admin
- Check Django logs: `question_generator` logger
- Check AI Worker logs on Colab

### No questions created
- Check `worker_response` in admin
- Verify AI Worker sent correct format
- Check `receive_ai_questions` logs

---

## 📚 Model Schema

### QuizTask
```python
- task_id (str): Unique ID from AI Worker
- user (FK): User who requested
- quiz_size (int): Number of questions requested
- status (str): queued, processing, completed, failed
- questions_created (int): Number saved to DB
- declared_level (str): English level
- preferred_topics (JSONField): List of topics
- weak_skills (JSONField): List of weak areas
- extra_instructions (str): Custom AI instructions
- created_at, started_at, completed_at (datetime)
- error_message (str): If failed
- worker_response (JSONField): Full AI Worker response
- processing_time_sec (int): Duration
```

### Question (existing)
```python
- text (TextField): Question content
- a, b, c, d (TextField): Answer options
- correct (CharField): Correct answer (A/B/C/D)
- explanation (TextField): Why correct
- difficulty (CharField): Level
- question_type (CharField): Type
- score (int): Points
- context (CharField): Domain
```

---

## 🎯 Next Steps

1. ✅ Models created + migrated
2. ✅ Views implemented
3. ✅ API endpoints ready
4. ✅ Admin dashboard setup
5. 📋 Frontend integration (optional)
6. 📊 Analytics + reporting (future)

---

## 📞 Support

Xem file: **IMPLEMENTATION_GUIDE.md** để hiểu chi tiết về cách hoạt động.
