# 🚀 Hướng Dẫn Tạo Câu Hỏi AI - Implementation Guide

## 📋 Giải Pháp Đề Xuất

Vì quá trình tạo câu hỏi rất lâu (3-10 phút), sẽ sử dụng **Async Task Queue Pattern**:

```
User Request
    ↓
1. Django nhận request → tạo QuizTask record → trả task_id
    ↓
2. AI Worker nhận request → xử lý trong background (3-10 phút)
    ↓
3. AI Worker hoàn tất → gửi kết quả về Django
    ↓
4. Django lưu câu hỏi vào DB → update QuizTask status
    ↓
5. User có thể check status hoặc auto-poll để biết khi nào xong
```

---

## 🔧 Cấu Trúc Model User & Database

### User Model (Hiện tại - Accounts App)
```python
class User(AbstractUser):
    declared_level: str (Beginner, Elementary, ..., Advanced)
    goals: str (study_abroad, job, exam, communication)
    profession: str (student, teacher, engineer, other)
    referred_frequency: str (daily, weekly, monthly)
    motivation_level: int (1-10)
    hobby: str (reading, movies, music, ...)
```

**Lưu ý:** Các trường trong payload request có thể được mapping từ User model hoặc nhận thêm từ request body.

### Question Model (Quiz App)
```python
class Question(models.Model):
    text: TextField              # Nội dung câu hỏi
    directive: TextField         # Hướng dẫn (optional)
    a, b, c, d: TextField        # 4 đáp án
    correct: CharField           # Đáp án đúng (A/B/C/D)
    explanation: TextField       # Giải thích
    question_type: CharField     # grammar, vocabulary, sentence_completion
    difficulty: CharField        # beginner, intermediate, advanced
    score: IntegerField          # 0-10 điểm
    context: CharField           # Lĩnh vực (coding, debugging, agile...)
    category: CharField          # Danh mục
```

---

## 📦 Tạo Model Tracking: QuizTask

Tạo model để tracking trạng thái công việc AI:

```python
# question_generator/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class QuizTask(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued - Chờ xử lý'),
        ('processing', 'Processing - Đang xử lý'),
        ('completed', 'Completed - Hoàn tất'),
        ('failed', 'Failed - Lỗi'),
    ]

    # Thông tin task
    task_id = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_tasks')
    
    # Thông tin request
    quiz_size = models.IntegerField(default=10)
    declared_level = models.CharField(max_length=50)
    profession = models.CharField(max_length=50, blank=True)
    preferred_topics = models.JSONField(default=list)
    weak_skills = models.JSONField(default=list)
    extra_instructions = models.TextField(blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    questions_created = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata từ AI Worker
    worker_response = models.JSONField(default=dict)
    
    def __str__(self):
        return f"QuizTask {self.task_id} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
```

**Chạy migration:**
```bash
python manage.py makemigrations question_generator
python manage.py migrate question_generator
```

---

## ✅ Điều Chỉnh Request Payload

### Request từ Client → Django

```python
payload = {
    # ⭐ User reference
    "user_id": "nhan_test_shell_026",  # hoặc user.id nếu là user đã login
    
    # ⭐ Quiz settings
    "quiz_size": 11,
    "declared_level": "Advanced",
    
    # 🔧 Optional: nếu muốn override user profile
    "english_level": "Advanced",       # optional, default dùng declared_level
    "goals": "job",                    # optional, default dùng user.goals
    "goal": "job",                     # redundant với goals
    "profession": "software engineer",  # optional, default dùng user.profession
    "job_role": "software engineer",   # redundant với profession
    
    # 📊 Learning profile
    "referred_frequency": "daily",     # optional
    "study_frequency": "daily",        # optional
    "motivation_level": "9",           # optional
    "hobby": "...",                    # optional
    
    # 🎯 Personalization
    "preferred_topics": [
        "cloud computing",
        "API design and integration",
        ...
    ],
    "weak_skills": [
        "subjunctive mood in formal requests",
        "gerunds vs infinitives",
        ...
    ],
    
    # 📝 Extra instructions for AI
    "extra_instructions": "Focus on realistic workplace scenarios..."
}
```

---

## 📤 Request Flow: Client → Django → AI Worker

### Step 1: Django nhận request từ client
```python
# POST /api/ai/generate/
def request_ai_questions(request):
    # 1. Validate input
    # 2. Get User object nếu user_id là integer
    # 3. Tạo QuizTask record (status='queued')
    # 4. Forward request tới AI Worker
    # 5. Return task_id cho client
```

### Step 2: AI Worker xử lý (3-10 phút)
- Nhận payload từ Django
- Tạo câu hỏi sử dụng LLM
- Đặt các câu hỏi vào queue

### Step 3: AI Worker gửi kết quả về Django
```python
# POST /api/ai/receive/
# Header: X-AI-Worker-Token: <token>
# Body:
{
    "worker_task_id": "task-xyz-123",
    "user_id": "nhan_test_shell_026",
    "questions": [
        {
            "sentence": "What is...",
            "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
            "correct_answer": "A",
            "explanation": "...",
            "type": "sentence_completion",
            "difficulty": "advanced",
            "score": 1,
            "context": "coding"
        },
        ...
    ],
    "meta": {
        "total_processed": 11,
        "processing_time_sec": 180
    }
}
```

### Step 4: Django lưu questions + update QuizTask
```python
# services.save_questions_to_db()
# - Tạo Question objects
# - Update QuizTask status → 'completed'
# - Return số lượng questions tạo
```

### Step 5: Client check status
```python
# GET /api/ai/tasks/<task_id>/
# Response:
{
    "task_id": "task-xyz-123",
    "status": "completed",
    "questions_created": 11,
    "progress": "100%",
    "created_at": "2026-01-23T10:30:00Z",
    "completed_at": "2026-01-23T10:38:00Z"
}
```

---

## 🧪 Test Script - Django Shell

```python
# python manage.py shell

from django.conf import settings
from django.contrib.auth import get_user_model
import requests
import json
import time

User = get_user_model()

# Tạo user hoặc get user tồn tại
user, created = User.objects.get_or_create(
    username="nhan_test_shell_026",
    defaults={
        "first_name": "Nhan",
        "declared_level": "Advanced",
        "goals": "job",
        "profession": "engineer",
        "motivation_level": 9,
    }
)
print(f"User: {user.username} (created={created})")

# Payload đầy đủ
payload = {
    "user_id": user.id,  # ⭐ Dùng id thay vì username
    "quiz_size": 11,
    "declared_level": "Advanced",
    "profession": "software engineer",
    "referred_frequency": "daily",
    "study_frequency": "daily",
    "motivation_level": 9,
    "hobby": "competitive programming",
    "preferred_topics": [
        "cloud computing",
        "API design",
        "debugging",
        "agile methodologies",
        "system security",
        "databases and SQL"
    ],
    "weak_skills": [
        "subjunctive mood",
        "gerunds vs infinitives",
        "prepositions in technical contexts",
        "past perfect tense"
    ],
    "extra_instructions": "Focus on realistic workplace scenarios. Prioritize code review and sprint retrospectives."
}

headers = {
    "Content-Type": "application/json",
    "X-AI-Worker-Token": settings.AI_WORKER_TOKEN
}

print("\n" + "="*70)
print("📤 GỬI REQUEST TỚI DJANGO")
print("="*70)
print(f"URL: {settings.BASE_URL}/api/ai/generate/")
print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

try:
    # 📌 SEND to Django (localhost)
    response = requests.post(
        f"{settings.BASE_URL}/api/ai/generate/",  # or ngrok if deployed
        json=payload,
        headers=headers,
        timeout=30  # Django should respond quickly
    )
    
    print(f"\n✅ Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 202:
        task_id = data.get("task_id")
        print(f"\n🎯 Task accepted! Task ID: {task_id}")
        print(f"\n⏳ AI Worker sẽ xử lý trong 3-10 phút...")
        print(f"📊 Bạn có thể check status hoặc check DB/log Colab.")
        
        # Optional: Poll status mỗi 30 giây
        print(f"\n--- Polling mỗi 30 giây (max 5 lần) ---")
        for i in range(5):
            time.sleep(30)
            # Status endpoint sẽ được implement sau
            print(f"Poll #{i+1}: [Chưa có endpoint, check DB thủ công]")
            
except Exception as e:
    print(f"❌ Error: {str(e)}")
```

---

## 📊 SQL Queries để kiểm tra

```sql
-- Xem tasks đang pending
SELECT * FROM question_generator_quiztask 
WHERE status IN ('queued', 'processing')
ORDER BY created_at DESC;

-- Xem tasks hoàn tất
SELECT * FROM question_generator_quiztask 
WHERE status = 'completed'
ORDER BY completed_at DESC;

-- Xem question được tạo
SELECT COUNT(*) as total_questions, difficulty, question_type
FROM quiz_question
WHERE created_at >= NOW() - INTERVAL 24 HOUR
GROUP BY difficulty, question_type;
```

---

## 🔄 Complete Flow Summary

| Step | Actor | Action | Timeout |
|------|-------|--------|---------|
| 1 | Client | Gửi request quiz generation | - |
| 2 | Django | Validate + Create QuizTask + Forward to AI Worker | 5 sec |
| 3 | Django | Return task_id (202 Accepted) | - |
| 4 | AI Worker | Process questions (LLM generation) | **3-10 min** |
| 5 | AI Worker | Send completed questions back to Django | - |
| 6 | Django | Receive, validate, save to DB | 5 sec |
| 7 | Django | Update QuizTask status → 'completed' | - |
| 8 | Client | Poll status endpoint / webhook callback | - |
| 9 | Client | Get task_id → Fetch questions từ API | - |

---

## ⚙️ Environment Variables

```bash
# .env
AI_WORKER_URL=https://nonelliptic-dewily-carlos.ngrok-free.dev
AI_WORKER_TOKEN=38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21
BASE_URL=http://localhost:8000  # Django server
```

---

## 🎯 Khuyến Nghị Best Practices

1. **Không block request** - Luôn return 202 Accepted sau khi forward tới AI Worker
2. **Database tracking** - Lưu task vào DB để debug + audit trail
3. **Timeout config** - Django timeout: 180s (forward), AI Worker timeout: 600s+ (processing)
4. **Error handling** - Implement retry logic nếu AI Worker fail
5. **Logging** - Log all requests, responses, errors for debugging
6. **Rate limiting** - Giới hạn số request per user per hour (future enhancement)

---

## 🔗 API Endpoints Cần Implement

```python
# ✅ Existing (cần cải tiến)
POST   /api/ai/generate/          # Request quiz generation
POST   /api/ai/receive/           # Receive from AI worker

# ❌ To-Do (cần thêm)
GET    /api/ai/tasks/             # List user's tasks
GET    /api/ai/tasks/<task_id>/   # Get task status
GET    /api/ai/tasks/<task_id>/questions/  # Get generated questions
DELETE /api/ai/tasks/<task_id>/   # Cancel/delete task
```

---

## 📝 Next Steps

1. ✅ Create `QuizTask` model
2. ✅ Update `request_ai_questions` view
3. ✅ Update `receive_ai_questions` view  
4. ✅ Create status endpoint
5. ✅ Add proper logging + error handling
6. ✅ Test with Django shell
7. ✅ Add frontend integration
