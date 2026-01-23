import requests
import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import save_questions_to_db

logger = logging.getLogger(__name__)

@csrf_exempt
def request_ai_questions(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_id = body.get("user_id")
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)

    payload = {
        "user_id": user_id,
        "quiz_size": body.get("quiz_size", 20),
        "declared_level": body.get("declared_level", "Advanced"),
        "profession": body.get("profession", "engineer"),
        "preferred_topics": body.get("preferred_topics", []),
        "weak_skills": body.get("weak_skills", []),
    }

    headers = {
        "Content-Type": "application/json",
        "X-AI-Worker-Token": settings.AI_WORKER_TOKEN  # nếu worker yêu cầu
    }

    try:
        res = requests.post(
            f"{settings.AI_WORKER_URL}/generate",
            json=payload,
            headers=headers,
            timeout=180
        )

        if res.status_code == 202:
            data = res.json()
            task_id = data.get("task_id")
            # TODO: Lưu task vào DB nếu bạn có model QuizTask
            # QuizTask.objects.create(task_id=task_id, user_id=user_id, status="queued")
            return JsonResponse({
                "status": "queued",
                "task_id": task_id,
                "message": "Quiz generation started. Check status later."
            }, status=202)

        else:
            return JsonResponse(res.json() or {"error": "Worker error"}, status=res.status_code)

    except requests.exceptions.Timeout:
        return JsonResponse({"error": "AI worker timeout – generation may still be processing"}, status=504)
    except Exception as e:
        logger.error(f"AI worker request failed: {str(e)}")
        return JsonResponse({"error": "AI worker unavailable"}, status=503)


@csrf_exempt  # đã có, nhưng cần chắc chắn áp dụng đúng
def receive_ai_questions(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # Bỏ hoàn toàn check CSRF token (vì đây là API từ worker, không phải browser)
    # Chỉ giữ lại check secret token để bảo mật
    token = request.headers.get("X-AI-Worker-Token")
    if token != settings.AI_WORKER_TOKEN:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    worker_task_id = data.get("worker_task_id")
    user_id = data.get("user_id")
    questions = data.get("questions", [])
    meta = data.get("meta", {})

    if not questions:
        return JsonResponse({"error": "questions list is empty"}, status=400)

    try:
        # Lưu questions
        save_questions_to_db(questions, user_id=user_id)  # truyền user_id nếu hàm cần

        # TODO: Update task status trong DB
        # task = QuizTask.objects.filter(task_id=worker_task_id).first()
        # if task:
        #     task.status = "completed"
        #     task.completed_at = timezone.now()
        #     task.meta = meta
        #     task.save()

        logger.info(f"Saved {len(questions)} questions for user {user_id} | task {worker_task_id}")
        return JsonResponse({
            "status": "ok",
            "saved": len(questions),
            "task_id": worker_task_id
        }, status=201)

    except Exception as e:
        logger.error(f"Error saving questions (task {worker_task_id}): {str(e)}")
        return JsonResponse({"error": "Failed to save questions"}, status=500)