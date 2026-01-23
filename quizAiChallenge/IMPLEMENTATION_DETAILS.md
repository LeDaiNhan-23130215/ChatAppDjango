# 📋 Chi Tiết Implementations - AI Quiz Generation System

## 🎯 Tóm Tắt Giải Pháp

**Vấn đề:** Quá trình tạo câu hỏi từ AI Worker rất lâu (3-10 phút), không thể block request.

**Giải Pháp:** Async Task Queue Pattern
- Django nhận request → tạo QuizTask → forward ngay tới AI Worker → return task_id (202)
- AI Worker xử lý trong background
- AI Worker gửi kết quả về Django → lưu questions → update status
- Client có thể check status qua API endpoint

---

## 📦 Các File Được Thay Đổi / Tạo Mới

### 1. ✅ `question_generator/models.py` - NEW
**Mục đích:** Định nghĩa QuizTask model để tracking công việc

**Nội dung chính:**
```python
class QuizTask(models.Model):
    # Identifiers
    task_id                # ID từ AI Worker
    user                   # FK tới User model
    
    # Request parameters (lưu lại để audit + retry)
    quiz_size              # Số câu hỏi
    declared_level         # Mức độ tiếng Anh
    profession             # Ngành nghề
    goals                  # Mục tiêu học
    preferred_topics       # JSON list
    weak_skills            # JSON list
    extra_instructions     # String
    
    # Status tracking
    status                 # queued, processing, completed, failed
    questions_created      # Số questions lưu vào DB
    error_message          # Nếu failed
    
    # Timestamps
    created_at             # Khi user request
    started_at             # Khi worker bắt đầu
    completed_at           # Khi hoàn tất
    
    # Metadata
    worker_response        # JSON response từ worker
    processing_time_sec    # Thời gian xử lý
```

**Phương thức:**
- `mark_processing()` - Cập nhật status → processing
- `mark_completed(questions_count)` - Cập nhật status → completed
- `mark_failed(error_msg)` - Cập nhật status → failed
- Properties: `is_completed`, `is_failed`, `is_pending`, `duration_seconds`

---

### 2. ✅ `question_generator/views.py` - UPDATED
**Mục đích:** Implement các API endpoints

**Endpoints:**

#### A. `request_ai_questions` - POST /api/ai/generate/
```python
Input:
{
    "user_id": 1,                    # Required: int hoặc string username
    "quiz_size": 10,                 # 1-100
    "declared_level": "Advanced",    # Optional: dùng user.declared_level nếu null
    "profession": "engineer",        # Optional
    "preferred_topics": [...],       # Optional: JSONField
    "weak_skills": [...],            # Optional: JSONField
    "extra_instructions": "...",     # Optional
    ...
}

Logic:
1. Validate JSON + user_id
2. Get User object (by ID hoặc username)
3. Create QuizTask record (status='queued')
4. Forward payload tới AI Worker
5. Update task_id + status='processing'
6. Return 202 + task_id

Output (202):
{
    "status": "queued",
    "task_id": "task-xyz-123",
    "message": "Quiz generation started...",
    "user_id": 1
}
```

**Xử lý lỗi:**
- 400: Invalid JSON, missing user_id
- 404: User not found
- 500: Task creation failed
- 503: AI Worker unavailable
- 504: Timeout

---

#### B. `receive_ai_questions` - POST /api/ai/receive/
```python
Input (from AI Worker):
{
    "worker_task_id": "task-xyz-123",
    "user_id": 1,
    "questions": [
        {
            "sentence": "...",
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
        "processing_time_sec": 180,
        "total_processed": 10
    }
}

Logic:
1. Validate X-AI-Worker-Token header
2. Validate JSON
3. Call save_questions_to_db() → tạo Question objects
4. Update QuizTask: status='completed', questions_created=X
5. Return 201 + summary

Output (201):
{
    "status": "ok",
    "saved": 10,
    "task_id": "task-xyz-123",
    "user_id": 1
}
```

**Xử lý lỗi:**
- 400: Invalid JSON, empty questions
- 401: Wrong token
- 500: Database error

---

#### C. `get_task_status` - GET /api/ai/tasks/<task_id>/
```python
Logic:
1. Get QuizTask by task_id
2. Return full status + metadata

Output (200):
{
    "task_id": "task-xyz-123",
    "status": "completed",  # queued, processing, completed, failed
    "user_id": 1,
    "questions_created": 10,
    "quiz_size_requested": 10,
    "created_at": "2026-01-23T10:30:00Z",
    "started_at": "2026-01-23T10:35:00Z",
    "completed_at": "2026-01-23T10:40:00Z",
    "duration_seconds": 600,
    "error_message": "",
    "is_completed": true,
    "is_failed": false,
    "is_pending": false
}
```

**Xử lý lỗi:**
- 404: Task not found

---

#### D. `list_user_tasks` - GET /api/ai/tasks/
```python
Query Parameters:
- user_id: (optional) Filter by user
- status: (optional) Filter by status
- limit: (optional) Number of tasks (default: 10)

Logic:
1. Build query với filters
2. Order by created_at DESC
3. Return list tasks

Output (200):
{
    "count": 5,
    "limit": 10,
    "tasks": [
        {
            "task_id": "task-xyz-123",
            "status": "completed",
            "user_id": 1,
            "quiz_size": 10,
            "questions_created": 10,
            "created_at": "...",
            "completed_at": "...",
            "duration_seconds": 600
        },
        ...
    ]
}
```

---

### 3. ✅ `question_generator/urls.py` - UPDATED
**Mục đích:** Map URLs tới views

**Routes:**
```python
POST   /api/ai/generate/              → request_ai_questions
POST   /api/ai/receive/               → receive_ai_questions (csrf_exempt)
GET    /api/ai/tasks/<task_id>/       → get_task_status
GET    /api/ai/tasks/                 → list_user_tasks
```

**Đầy đủ:**
```
/api/ai/generate/            - Request quiz (return 202 + task_id)
/api/ai/receive/             - Receive from worker (called by AI)
/api/ai/tasks/<task_id>/     - Get task status
/api/ai/tasks/               - List user tasks (with filters)
```

---

### 4. ✅ `question_generator/admin.py` - UPDATED
**Mục đích:** Django Admin interface cho QuizTask

**Features:**
- List view: task_id, user, status (color badge), questions_created, duration, created_at
- Search: task_id, username, email
- Filter: status, created_at, declared_level
- Detail view:
  - Task Info
  - Request Parameters
  - Status & Results
  - Timestamps (collapsed)
  - Worker Response JSON (collapsed)
- Read-only: task_id, timestamps, worker_response
- Permission: Only superuser can delete

**Admin URL:**
```
http://localhost:8000/admin/question_generator/quiztask/
```

---

### 5. ✅ Migration File
**Location:** `question_generator/migrations/0001_initial.py`

**Command:**
```bash
python manage.py makemigrations question_generator
python manage.py migrate question_generator
```

**Tạo bảng:** `question_generator_quiztask` với:
- Primary key: id
- Unique: task_id
- Indexes: (user, -created_at), (status, -created_at), (task_id)
- Foreign key: user_id → auth_user.id (CASCADE)

---

## 📄 Các File Hướng Dẫn Được Tạo

### 1. `IMPLEMENTATION_GUIDE.md`
**Nội dung:**
- Giải thích chi tiết về Async pattern
- Model structure & payload format
- Complete flow diagram
- Test script có hướng dẫn
- SQL queries để verify
- Best practices

---

### 2. `QUICK_START.md`
**Nội dung:**
- 5 phút setup guide
- Copy-paste test commands
- API endpoints cheat sheet
- Troubleshooting

---

### 3. `test_quiz_generation_complete.py`
**Mục đích:** Full test script (có thể chạy standalone)

**Features:**
- Step 1-5: Create user → Send request → Poll status
- Polling loop mỗi 30 giây
- Database summary
- Final instructions

**Chạy:**
```bash
python manage.py shell
>>> exec(open('test_quiz_generation_complete.py').read())
```

---

### 4. `test_quiz_simple.py`
**Mục đích:** Quick test script cho Django shell

**Nội dung:**
- 6 steps đơn giản
- Inline instructions

**Chạy:**
```bash
python manage.py shell
>>> exec(open('test_quiz_simple.py').read())
```

---

## 🔄 Request Flow Chi Tiết

### Timeline

```
T=0s:   User gửi request POST /api/ai/generate/
        │
        ├─ Django validate input
        ├─ Get User object
        ├─ Create QuizTask (status='queued')
        ├─ Forward tới AI Worker
        └─ Return 202 + task_id (< 1 giây)
        
T=1-5s: AI Worker nhận request
        │
        ├─ Validate
        └─ Thêm vào processing queue
        
T=5-600s: AI Worker xử lý
         │
         ├─ Load LLM model
         ├─ Generate questions (3-10 phút)
         └─ POST /api/ai/receive/ tới Django
         
T=600s: Django nhận kết quả
        │
        ├─ Validate token
        ├─ save_questions_to_db() → bulk create Questions
        ├─ Update QuizTask: status='completed'
        └─ Return 201 OK
        
T=600+: Client check status
        │
        ├─ GET /api/ai/tasks/<task_id>/
        └─ Nhận questions_created=10, status='completed'
```

---

## 📊 Database Schema

### QuizTask Table
```
Column                  Type            Constraints
────────────────────────────────────────────────────
id                      INTEGER         PK
task_id                 VARCHAR(100)    UNIQUE, INDEX
user_id                 INTEGER         FK auth_user, CASCADE
quiz_size               INTEGER         DEFAULT 10
declared_level          VARCHAR(50)
profession              VARCHAR(100)
goals                   VARCHAR(50)
preferred_topics        JSON            DEFAULT []
weak_skills             JSON            DEFAULT []
extra_instructions      TEXT
status                  VARCHAR(20)     INDEX (queued|processing|completed|failed)
questions_created       INTEGER         DEFAULT 0
error_message           TEXT
created_at              DATETIME        AUTO
started_at              DATETIME        NULL
completed_at            DATETIME        NULL
worker_response         JSON            DEFAULT {}
processing_time_sec     INTEGER         NULL

Indexes:
- idx_task_id (task_id)
- idx_user_created (user_id, -created_at)
- idx_status_created (status, -created_at)
```

### Question Table (Existing - được sử dụng)
```
Được mapping từ AI Worker response:
{
    "sentence" → text
    "options" → a, b, c, d
    "correct_answer" → correct
    "explanation" → explanation
    "type" → question_type
    "difficulty" → difficulty
    "score" → score
    "context" → context
}
```

---

## 🔐 Security

### Token Validation
- Endpoint `/api/ai/receive/` kiểm tra header `X-AI-Worker-Token`
- So sánh với `settings.AI_WORKER_TOKEN`
- Return 401 nếu không match

### CSRF
- POST `/api/ai/generate/` có `@csrf_exempt` (accept từ Postman/scripts)
- POST `/api/ai/receive/` có `@csrf_exempt` (AI Worker gọi từ server)
- GET endpoints không cần CSRF

### Input Validation
- JSON parsing with try/except
- User existence check
- quiz_size range validation (1-100)
- Required field checks

---

## 📈 Monitoring & Debugging

### Admin Dashboard
```
http://localhost:8000/admin/question_generator/quiztask/
- Real-time status monitoring
- Worker response inspection
- Duration tracking
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)
# quizAiChallenge/settings.py định nghĩa logger cho question_generator
```

### Database Queries
```python
# Check pending tasks
QuizTask.objects.filter(status__in=['queued', 'processing'])

# Check completed tasks
QuizTask.objects.filter(status='completed').order_by('-completed_at')

# Check failed tasks
QuizTask.objects.filter(status='failed')

# Get task details
task = QuizTask.objects.get(task_id='task-xyz-123')
print(task.status, task.questions_created, task.error_message)
```

---

## 🚀 Deployment Checklist

- [ ] Migration chạy: `python manage.py migrate`
- [ ] Endpoints tested: `GET /api/ai/tasks/`, `POST /api/ai/generate/`
- [ ] Admin accessible: `http://localhost:8000/admin/`
- [ ] AI Worker endpoint configured: `settings.AI_WORKER_URL`
- [ ] AI Worker token set: `settings.AI_WORKER_TOKEN`
- [ ] Logging configured: check Django logs
- [ ] Database indexed: Performance optimization

---

## 🔗 Related Files (Unchanged)

- `question_generator/services.py` - save_questions_to_db() (existing, tested)
- `quiz/models.py` - Question model (used for storage)
- `accounts/models.py` - User model (FK reference)
- `quizAiChallenge/settings.py` - Settings (AI_WORKER_URL, TOKEN)
- `quizAiChallenge/urls.py` - URL config (already includes /api/ai/)

---

## ✨ Features Implemented

✅ Async task tracking
✅ Database persistence
✅ Status polling endpoint
✅ List user tasks with filters
✅ Token-based security
✅ Error handling & logging
✅ Admin dashboard
✅ Comprehensive test scripts
✅ Migration framework

---

## 🎯 Next Steps (Future)

- [ ] Webhook callbacks (notify client when completed)
- [ ] Rate limiting per user
- [ ] Task cancellation endpoint
- [ ] Retry logic for failed tasks
- [ ] WebSocket for real-time updates
- [ ] Frontend integration
- [ ] Analytics dashboard
- [ ] Pagination for task listing

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Create migrations | `python manage.py makemigrations question_generator` |
| Apply migrations | `python manage.py migrate` |
| Test | `python manage.py shell < test_quiz_simple.py` |
| View admin | `http://localhost:8000/admin/question_generator/quiztask/` |
| Check API | `curl http://localhost:8000/api/ai/tasks/` |
