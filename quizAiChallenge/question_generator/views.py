import requests
import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.utils import timezone
from .services import save_questions_to_db
from .models import QuizTask

logger = logging.getLogger(__name__)
User = get_user_model()

@csrf_exempt
def request_ai_questions(request):
    """
    Request quiz generation from AI worker.
    
    Request flow:
    1. Client sends POST with user_id + quiz parameters
    2. Django validates input + gets User object
    3. Django creates QuizTask (status='queued')
    4. Django forwards to AI worker
    5. Return task_id immediately (202 Accepted)
    
    Note: AI worker processes asynchronously (3-10 minutes)
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in request_ai_questions")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Extract and validate user_id
    user_id = body.get("user_id")
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)

    # Get user object - handle both int ID and string username
    user = None
    try:
        if isinstance(user_id, int):
            user = User.objects.get(id=user_id)
        else:
            # Try as username first
            user = User.objects.get(username=str(user_id))
    except User.DoesNotExist:
        logger.warning(f"User not found: {user_id}")
        return JsonResponse({"error": f"User not found: {user_id}"}, status=404)

    # Build payload for AI worker with validation
    quiz_size = int(body.get("quiz_size", 10))
    if quiz_size < 1 or quiz_size > 100:
        return JsonResponse({"error": "quiz_size must be between 1 and 100"}, status=400)

    # Use user profile if not provided in request
    declared_level = body.get("declared_level") or user.declared_level or "Intermediate"
    goals = body.get("goals") or body.get("goal") or user.goals or "job"
    profession = body.get("profession") or body.get("job_role") or user.profession or ""

    payload = {
        "user_id": user.id,  # Send user.id to AI worker
        "quiz_size": quiz_size,
        "declared_level": declared_level,
        "goals": goals,
        "profession": profession,
        "preferred_topics": body.get("preferred_topics", []),
        "weak_skills": body.get("weak_skills", []),
        "extra_instructions": body.get("extra_instructions", ""),
        # Optional fields
        "study_frequency": body.get("study_frequency") or user.referred_frequency,
        "motivation_level": body.get("motivation_level"),
    }

    # Create QuizTask record BEFORE forwarding to worker
    # This allows tracking even if worker fails
    task_id = f"task-{user.id}-{int(timezone.now().timestamp() * 1000)}"
    
    try:
        quiz_task = QuizTask.objects.create(
            task_id=task_id,
            user=user,
            quiz_size=quiz_size,
            declared_level=declared_level,
            goals=goals,
            profession=profession,
            preferred_topics=payload.get("preferred_topics", []),
            weak_skills=payload.get("weak_skills", []),
            extra_instructions=payload.get("extra_instructions", ""),
            status='queued'
        )
        logger.info(f"Created QuizTask: {task_id} for user {user.username}")
    except Exception as e:
        logger.error(f"Error creating QuizTask: {str(e)}")
        return JsonResponse({"error": "Failed to create task record"}, status=500)

    # Forward to AI worker
    headers = {
        "Content-Type": "application/json",
        "X-AI-Worker-Token": settings.AI_WORKER_TOKEN
    }

    try:
        logger.info(f"Forwarding to AI worker: {settings.AI_WORKER_URL}/generate")
        res = requests.post(
            f"{settings.AI_WORKER_URL}/generate",
            json=payload,
            headers=headers,
            timeout=30  # Django timeout - just forwarding
        )

        if res.status_code == 202:
            data = res.json()
            worker_task_id = data.get("task_id")
            
            # Update QuizTask with worker's task_id for reference
            quiz_task.task_id = worker_task_id  # Update with actual worker task_id
            quiz_task.status = 'processing'
            quiz_task.save(update_fields=['task_id', 'status'])
            
            logger.info(f"Task accepted by worker: {worker_task_id}")
            return JsonResponse({
                "status": "queued",
                "task_id": worker_task_id,
                "message": "Quiz generation started. Estimated time: 3-10 minutes",
                "user_id": user.id,
            }, status=202)

        else:
            quiz_task.mark_failed(f"Worker error: {res.status_code}")
            logger.error(f"Worker error: {res.status_code} - {res.text}")
            return JsonResponse(
                res.json() or {"error": "Worker error"}, 
                status=res.status_code
            )

    except requests.exceptions.Timeout:
        quiz_task.mark_failed("Request timeout to AI worker")
        logger.error("Timeout connecting to AI worker")
        return JsonResponse(
            {"error": "AI worker timeout – generation may still be processing"}, 
            status=504
        )
    except Exception as e:
        quiz_task.mark_failed(str(e))
        logger.error(f"AI worker request failed: {str(e)}")
        return JsonResponse(
            {"error": "AI worker unavailable"}, 
            status=503
        )


@csrf_exempt
def receive_ai_questions(request):
    """
    Receive completed questions from AI worker.
    
    Called by AI worker after processing (3-10 minutes).
    Expected format:
    {
        "worker_task_id": "task-xyz-123",
        "user_id": 1,
        "questions": [...],
        "meta": {"processing_time_sec": 180, "total_processed": 10}
    }
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # Validate token - this is from AI worker, not browser
    token = request.headers.get("X-AI-Worker-Token")
    if token != settings.AI_WORKER_TOKEN:
        logger.warning(f"Unauthorized token in receive_ai_questions")
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in receive_ai_questions")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Extract required fields
    worker_task_id = data.get("worker_task_id")
    user_id = data.get("user_id")
    questions = data.get("questions", [])
    meta = data.get("meta", {})

    if not questions:
        logger.warning(f"Empty questions list for task {worker_task_id}")
        return JsonResponse({"error": "questions list is empty"}, status=400)

    if not user_id:
        logger.warning(f"Missing user_id in receive_ai_questions")
        return JsonResponse({"error": "user_id is required"}, status=400)

    # Get QuizTask
    try:
        quiz_task = QuizTask.objects.get(task_id=worker_task_id)
    except QuizTask.DoesNotExist:
        logger.warning(f"QuizTask not found: {worker_task_id}")
        # Still save questions but log warning
        quiz_task = None

    try:
        # Save questions to database
        created_count = save_questions_to_db(questions, user_id=user_id)
        logger.info(f"Saved {created_count} questions for user {user_id}")

        # Update QuizTask status
        if quiz_task:
            processing_time = meta.get("processing_time_sec", 0)
            quiz_task.mark_completed(
                questions_count=created_count,
                processing_time_sec=processing_time
            )
            quiz_task.worker_response = data  # Store full response for audit
            quiz_task.save(update_fields=['worker_response'])
            
            logger.info(f"Updated QuizTask {worker_task_id}: completed with {created_count} questions")

        return JsonResponse({
            "status": "ok",
            "saved": created_count,
            "task_id": worker_task_id,
            "user_id": user_id,
        }, status=201)

    except Exception as e:
        logger.error(f"Error saving questions (task {worker_task_id}): {str(e)}")
        if quiz_task:
            quiz_task.mark_failed(f"Error saving questions: {str(e)}")
        return JsonResponse({
            "error": "Failed to save questions",
            "details": str(e)
        }, status=500)


@csrf_exempt
def get_task_status(request, task_id):
    """
    Get status of a quiz generation task.
    
    Returns:
    {
        "task_id": "task-xyz-123",
        "status": "completed",  # queued, processing, completed, failed
        "questions_created": 10,
        "created_at": "2026-01-23T10:30:00Z",
        "completed_at": "2026-01-23T10:38:00Z",
        "duration_seconds": 480,
        "error_message": ""
    }
    """
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    try:
        quiz_task = QuizTask.objects.get(task_id=task_id)
    except QuizTask.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    return JsonResponse({
        "task_id": quiz_task.task_id,
        "status": quiz_task.status,
        "user_id": quiz_task.user.id,
        "questions_created": quiz_task.questions_created,
        "quiz_size_requested": quiz_task.quiz_size,
        "created_at": quiz_task.created_at.isoformat(),
        "started_at": quiz_task.started_at.isoformat() if quiz_task.started_at else None,
        "completed_at": quiz_task.completed_at.isoformat() if quiz_task.completed_at else None,
        "duration_seconds": quiz_task.duration_seconds,
        "error_message": quiz_task.error_message,
        "is_completed": quiz_task.is_completed,
        "is_failed": quiz_task.is_failed,
        "is_pending": quiz_task.is_pending,
    }, status=200)


@csrf_exempt
def list_user_tasks(request):
    """
    List all tasks for the current user or a specific user.
    
    Query parameters:
    - user_id: (optional) Filter by user ID
    - status: (optional) Filter by status (queued, processing, completed, failed)
    - limit: (optional) Number of tasks to return (default: 10)
    """
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    # Extract query parameters
    user_id = request.GET.get("user_id")
    status_filter = request.GET.get("status")
    limit = int(request.GET.get("limit", 10))

    # Build query
    query = QuizTask.objects.all()
    
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            query = query.filter(user=user)
        except User.DoesNotExist:
            return JsonResponse({"error": f"User not found: {user_id}"}, status=404)
    
    if status_filter:
        valid_statuses = [s[0] for s in QuizTask.STATUS_CHOICES]
        if status_filter not in valid_statuses:
            return JsonResponse({
                "error": f"Invalid status: {status_filter}. Valid: {valid_statuses}"
            }, status=400)
        query = query.filter(status=status_filter)

    # Order and limit
    tasks = query.order_by('-created_at')[:limit]

    tasks_data = [{
        "task_id": task.task_id,
        "status": task.status,
        "user_id": task.user.id,
        "quiz_size": task.quiz_size,
        "questions_created": task.questions_created,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "duration_seconds": task.duration_seconds,
    } for task in tasks]

    return JsonResponse({
        "count": len(tasks_data),
        "limit": limit,
        "tasks": tasks_data
    }, status=200)