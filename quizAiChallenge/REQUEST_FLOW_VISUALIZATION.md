# 🔄 Request Flow Visualization - AI Quiz Generation

## Complete Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REQUEST FLOW DIAGRAM                               │
└─────────────────────────────────────────────────────────────────────────────┘

                               CLIENT/USER
                                    │
                                    │ 1. POST /api/ai/generate/
                                    │    {user_id, quiz_size, topics, ...}
                                    │
                                    ▼
                        ╔════════════════════════╗
                        │   DJANGO APP           │
                        │   request_ai_questions │
                        ╚════════════════════════╝
                                    │
            ┌───────────┬───────────┼───────────┬───────────┐
            │           │           │           │           │
            ▼           ▼           ▼           ▼           ▼
        Validate    Get User    Create      Forward to   Return 202
        JSON        Object      QuizTask     AI Worker    + task_id
                                (DB)
                                    │
                                    │ 2a. POST /generate
                                    │    (forward payload)
                                    │
                                    ▼
                        ╔════════════════════════╗
                        │   AI WORKER (Colab)    │
                        │   (3-10 MINUTES)       │
                        ╚════════════════════════╝
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
                 Process        Generate       Save to
                 Payload        Questions      Cache
                                (LLM)
                                    │
                                    │ 3. POST /api/ai/receive/
                                    │    {task_id, questions[], ...}
                                    │
                                    ▼
                        ╔════════════════════════╗
                        │   DJANGO APP           │
                        │  receive_ai_questions  │
                        ╚════════════════════════╝
                                    │
            ┌───────────┬───────────┼───────────┬───────────┐
            │           │           │           │           │
            ▼           ▼           ▼           ▼           ▼
        Validate    Bulk Create  Update       Log          Return
        Token       Questions    QuizTask     Response     201 OK
                    (DB)         Status
                                    │
                                    ▼
                        ╔════════════════════════╗
                        │   DATABASE             │
                        │   (PostgreSQL)         │
                        ╚════════════════════════╝
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
                QuizTask        Question        Question
                Records         Table #1        Table #2
                (completed)     (record 1)      (record 2)
                                    │
                                    │ 4. GET /api/ai/tasks/<task_id>/
                                    │    (client polls)
                                    │
                                    ▼
                        ╔════════════════════════╗
                        │   DJANGO APP           │
                        │    get_task_status     │
                        ╚════════════════════════╝
                                    │
                                    ▼ Return full status
                                 CLIENT
```

---

## Detailed Request/Response Examples

### STEP 1: Client → Django (POST /api/ai/generate/)

```
REQUEST
=======

POST http://localhost:8000/api/ai/generate/
Content-Type: application/json

{
    "user_id": 1,
    "quiz_size": 11,
    "declared_level": "Advanced",
    "goals": "job",
    "profession": "software engineer",
    "referred_frequency": "daily",
    "motivation_level": 9,
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
    "extra_instructions": "Focus on realistic workplace scenarios..."
}


RESPONSE (202 Accepted)
=======================

{
    "status": "queued",
    "task_id": "task-1-1674470400000",
    "message": "Quiz generation started. Estimated time: 3-10 minutes",
    "user_id": 1
}

⏱️ Response Time: < 1 second
```

---

### STEP 2: Django → AI Worker (Internal Forward)

```
Django receives task_id from AI Worker's initial /generate endpoint,
updates the QuizTask record with this ID and continues processing.

Database State AFTER STEP 1:
=============================

QuizTask Record:
{
    "id": 1,
    "task_id": "task-1-1674470400000",
    "user_id": 1,
    "status": "processing",
    "quiz_size": 11,
    "declared_level": "Advanced",
    "preferred_topics": ["cloud computing", "API design", ...],
    "questions_created": 0,
    "created_at": "2026-01-23T10:30:00Z",
    "started_at": "2026-01-23T10:30:05Z",
    "completed_at": null,
    "error_message": ""
}
```

---

### STEP 3: AI Worker → Django (POST /api/ai/receive/)

```
REQUEST (from AI Worker after 3-10 minutes)
=============================================

POST http://localhost:8000/api/ai/receive/
Content-Type: application/json
X-AI-Worker-Token: 38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21

{
    "worker_task_id": "task-1-1674470400000",
    "user_id": 1,
    "questions": [
        {
            "sentence": "In a software company, during a sprint retrospective, "
                        "your team discusses improving the code review process. "
                        "Which statement is MOST appropriate?",
            "options": {
                "A": "The reviewer should approve all changes without examining them.",
                "B": "Code reviews should focus on finding potential bugs, security issues, "
                     "and maintaining code standards.",
                "C": "Only senior developers are responsible for reviewing code.",
                "D": "Code reviews are a waste of time and should be skipped."
            },
            "correct_answer": "B",
            "explanation": "Effective code reviews prevent bugs, security vulnerabilities, "
                          "and maintain code quality. All team members should participate.",
            "type": "sentence_completion",
            "difficulty": "advanced",
            "score": 1,
            "context": "agile meeting and code review"
        },
        // ... 10 more questions ...
    ],
    "meta": {
        "processing_time_sec": 315,
        "total_processed": 11
    }
}


RESPONSE (201 Created)
======================

{
    "status": "ok",
    "saved": 11,
    "task_id": "task-1-1674470400000",
    "user_id": 1
}

⏱️ Response Time: < 1 second
```

---

### Database State AFTER STEP 3

```
QuizTask Record (UPDATED):
===========================

{
    "id": 1,
    "task_id": "task-1-1674470400000",
    "user_id": 1,
    "status": "completed",              ← Changed from "processing"
    "quiz_size": 11,
    "declared_level": "Advanced",
    "preferred_topics": [...],
    "questions_created": 11,            ← Updated count
    "created_at": "2026-01-23T10:30:00Z",
    "started_at": "2026-01-23T10:30:05Z",
    "completed_at": "2026-01-23T10:35:15Z",  ← Set
    "error_message": "",
    "processing_time_sec": 315,         ← Set
    "worker_response": {
        "worker_task_id": "...",
        "user_id": 1,
        "questions": [...],
        "meta": {...}
    }
}


Question Records (NEW - 11 records):
====================================

Record 1:
{
    "id": 1,
    "text": "In a software company, during a sprint retrospective, ...",
    "a": "The reviewer should approve all changes without examining them.",
    "b": "Code reviews should focus on finding potential bugs, ...",
    "c": "Only senior developers are responsible for reviewing code.",
    "d": "Code reviews are a waste of time and should be skipped.",
    "correct": "B",
    "explanation": "Effective code reviews prevent bugs, security vulnerabilities, ...",
    "question_type": "sentence_completion",
    "difficulty": "advanced",
    "score": 1,
    "context": "agile meeting and code review"
}

Record 2:
{ ... similar structure ... }

... Record 3-11 ...
```

---

### STEP 4: Client → Django (GET /api/ai/tasks/<task_id>/)

```
REQUEST (client polls status anytime)
======================================

GET http://localhost:8000/api/ai/tasks/task-1-1674470400000/


RESPONSE (200 OK)
=================

{
    "task_id": "task-1-1674470400000",
    "status": "completed",
    "user_id": 1,
    "questions_created": 11,
    "quiz_size_requested": 11,
    "created_at": "2026-01-23T10:30:00Z",
    "started_at": "2026-01-23T10:30:05Z",
    "completed_at": "2026-01-23T10:35:15Z",
    "duration_seconds": 315,
    "error_message": "",
    "is_completed": true,
    "is_failed": false,
    "is_pending": false
}

⏱️ Response Time: < 100ms (direct DB query)
```

---

## Status Progression Timeline

```
T=0s:   Client sends request
        │
        ├─ Django validates
        ├─ Creates QuizTask
        ├─ Status: "queued"
        └─ Forwards to AI Worker

T=0-5s: Django returns 202 to client
        AI Worker receives request

T=5-600s: AI Worker processes
          Status: "processing"
          (LLM generation, takes 3-10 minutes)

T=600s: AI Worker sends results back
        Django receives + saves questions
        Status: "completed"
        Questions: 11

T=600+: Client checks status
        ✓ Status: completed
        ✓ Questions: 11
        ✓ Duration: 315 seconds
```

---

## Error Handling Flow

```
IF ERROR at Django (request_ai_questions):
════════════════════════════════════════

400 Bad Request
├─ Invalid JSON
├─ Missing user_id
└─ quiz_size out of range


404 Not Found
└─ User not found


500 Internal Server Error
└─ Failed to create QuizTask


503 Service Unavailable
└─ AI Worker not responding


504 Gateway Timeout
└─ AI Worker timeout


IF ERROR at Django (receive_ai_questions):
═══════════════════════════════════════════

400 Bad Request
├─ Invalid JSON
├─ Empty questions list
└─ Missing user_id


401 Unauthorized
└─ Wrong X-AI-Worker-Token


500 Internal Server Error
├─ Database error
└─ Question creation failed


Database Update on Error:
═════════════════════════

QuizTask Status → "failed"
QuizTask error_message → Error description
completed_at → Current timestamp
```

---

## Payload Mapping

```
CLIENT REQUEST             →  AI WORKER PAYLOAD       →  QUESTION RECORD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

user_id                    →  user_id                 →  (via FK)
quiz_size                  →  quiz_size               →  (stored in QuizTask)
declared_level             →  declared_level          →  (stored in QuizTask)
preferred_topics           →  preferred_topics        →  (stored in QuizTask)
weak_skills                →  weak_skills             →  (stored in QuizTask)
extra_instructions         →  extra_instructions      →  (stored in QuizTask)

                                                     ←  sentence (from response)
                                                     ←  options A-D
                                                     ←  correct_answer
                                                     ←  explanation
                                                     ←  type
                                                     ←  difficulty
                                                     ←  score
                                                     ←  context
```

---

## Database Relationships

```
┌──────────────────────┐
│      User            │
│  (accounts_user)     │
├──────────────────────┤
│ id (PK)              │
│ username             │
│ declared_level       │
│ goals                │
│ profession           │
└──────────┬───────────┘
           │ 1:N
           │
           ▼
┌──────────────────────┐
│    QuizTask          │
│ (question_generator) │
├──────────────────────┤
│ id (PK)              │
│ task_id (UNIQUE)     │◄──────── AI Worker reference
│ user_id (FK) ────────┘
│ quiz_size            │
│ status               │
│ questions_created    │
│ created_at           │
│ completed_at         │
│ worker_response      │
└──────────┬───────────┘
           │ 1:N (via created_at)
           │
           ▼
┌──────────────────────┐
│    Question          │
│    (quiz_question)   │
├──────────────────────┤
│ id (PK)              │
│ text                 │
│ a, b, c, d           │
│ correct              │
│ explanation          │
│ question_type        │
│ difficulty           │
│ score                │
│ context              │
└──────────────────────┘
```

---

## Key Differences: Sync vs Async

```
❌ SYNC (BLOCKING)          ✅ ASYNC (NON-BLOCKING)
─────────────────────────────────────────────────────

Client Request              Client Request
     ↓                           ↓
Wait 10 minutes           Return 202 (1 second)
(browser timeout?)        + task_id
     ↓                           ↓
Get Response              Check status anytime
     ↓                      (polling/webhook)
Done                            ↓
                          Get results when ready

Problem: HTTP timeout      Benefit:
- Browsers timeout at      - Fast response
  5-10 minutes            - Scalable
- No feedback             - Better UX
- Bad UX                  - Real-time updates
                          - Fault tolerant
```

---

## Monitoring Example

```
Admin Dashboard: http://localhost:8000/admin/question_generator/quiztask/

┌────────────────────────────────────────────────────────────────────────┐
│ Task ID          User        Status        Questions    Duration   Time │
├────────────────────────────────────────────────────────────────────────┤
│ task-1-167447... nhan_test   ✓ COMPLETED   11/11       315s      5.2m │
│ task-2-167447... john_dev    ⏳ PROCESSING  0/15        ...       2m   │
│ task-3-167447... alice_test  ❌ FAILED      0/10        -         10s  │
│ task-4-167446... bob_user    ⏸ QUEUED      0/20        ...       1s   │
└────────────────────────────────────────────────────────────────────────┘

Click row → View full details:
- Full worker response JSON
- Error messages
- Request parameters
- Exact timestamps
```

---

## API Usage Examples

### Example 1: Simple Test
```bash
# Create user
curl -X POST http://localhost:8000/admin/auth/user/add/

# Generate quiz
curl -X POST http://localhost:8000/api/ai/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "quiz_size": 5,
    "declared_level": "Advanced"
  }'

# Check status every 30 seconds
curl http://localhost:8000/api/ai/tasks/task-1-1674470400000/

# Check if completed
curl http://localhost:8000/api/ai/tasks/task-1-1674470400000/ | jq '.status'
```

### Example 2: Full Test Script
```python
import requests
import time

# Create task
response = requests.post('http://localhost:8000/api/ai/generate/', json={
    'user_id': 1,
    'quiz_size': 10,
    'declared_level': 'Advanced'
})
task_id = response.json()['task_id']

# Poll until completed
for i in range(20):
    r = requests.get(f'http://localhost:8000/api/ai/tasks/{task_id}/')
    status = r.json()['status']
    if status == 'completed':
        print(f"✓ {r.json()['questions_created']} questions created in {r.json()['duration_seconds']}s")
        break
    print(f"[{i+1}] Status: {status}")
    time.sleep(30)
```

---

## Performance Notes

- Request validation: < 100ms
- DB writes: < 200ms per question (bulk create optimized)
- Status check: < 50ms
- AI processing: 3-10 minutes (external service)
- Total end-to-end: ~3-10 minutes + response times

