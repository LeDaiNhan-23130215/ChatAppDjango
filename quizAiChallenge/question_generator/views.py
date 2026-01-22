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
    """
    Django → AI worker
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Validate required fields
    user_id = body.get("user_id")
    if not user_id:
        logger.error("Missing user_id")
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
        "X-AI-Worker-Token": settings.AI_WORKER_TOKEN
    }

    try:
        logger.info(f"Requesting questions from AI worker for user {user_id}")
        res = requests.post(
            f"{settings.AI_WORKER_URL}/generate",
            json=payload,
            headers=headers,
            timeout=10
        )
        return JsonResponse(res.json(), status=res.status_code)
    except Exception as e:
        logger.error(f"AI worker request failed: {str(e)}")
        return JsonResponse({"error": "AI worker unavailable"}, status=503)


@csrf_exempt
def receive_ai_questions(request):
    """
    AI worker → Django
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # Security check
    token = request.headers.get("X-AI-Worker-Token")
    if token != settings.AI_WORKER_TOKEN:
        logger.warning("Unauthorized request to receive_ai_questions")
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in receive_ai_questions")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    questions = data.get("questions", [])
    user_id = data.get("user_id")

    if not questions:
        logger.warning("No questions received")
        return JsonResponse({"error": "questions list is empty"}, status=400)

    try:
        logger.info(f"Saving {len(questions)} questions for user {user_id}")
        save_questions_to_db(questions)
        logger.info(f"Successfully saved {len(questions)} questions")
        return JsonResponse({
            "status": "ok",
            "saved": len(questions)
        }, status=201)
    except Exception as e:
        logger.error(f"Error saving questions: {str(e)}")
        return JsonResponse({"error": "Failed to save questions"}, status=500)
