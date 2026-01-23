"""
API endpoints để tạo câu hỏi từ AI Worker
Integrated trong quiz_ai_battle app
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .ai_question_service import generate_ai_question_async, get_question_from_task

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def generate_question(request):
    """
    API endpoint: Tạo câu hỏi từ AI Worker
    
    POST /user-vs-ai/api/generate-question/
    
    Request:
    {
        "difficulty": "easy|medium|hard|advanced"  (default: "medium")
    }
    
    Response:
    {
        "success": true,
        "task_id": "task-1-xxx",
        "message": "Question generation started",
        "estimated_time": "3-10 minutes"
    }
    """
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        }, status=400)
    
    difficulty = data.get('difficulty', 'medium')
    valid_difficulties = ['easy', 'medium', 'hard', 'advanced']
    
    if difficulty not in valid_difficulties:
        return JsonResponse({
            "success": False,
            "error": f"Invalid difficulty. Must be one of: {valid_difficulties}"
        }, status=400)
    
    # Generate question async
    result = generate_ai_question_async(request.user, difficulty)
    
    status_code = 202 if result['success'] else 400
    return JsonResponse(result, status=status_code)


@login_required
@require_http_methods(["GET"])
def check_question_status(request, task_id):
    """
    API endpoint: Check status của task
    
    GET /user-vs-ai/api/question-status/<task_id>/
    
    Response:
    {
        "success": true,
        "status": "queued|processing|completed|failed",
        "question": {...} (nếu completed),
        "message": "..."
    }
    """
    
    result = get_question_from_task(task_id, request.user)
    
    status_code = 200 if result['success'] else 400
    return JsonResponse(result, status=status_code, safe=False)


@login_required
@require_http_methods(["POST"])
def create_match_with_ai_question(request):
    """
    API endpoint: Tạo match + generate câu hỏi từ AI
    
    POST /user-vs-ai/api/create-match/
    
    Request:
    {
        "difficulty": "easy|medium|hard|advanced",
        "ai_mode": "random|gpt",
        "num_rounds": 5
    }
    
    Response:
    {
        "success": true,
        "match_id": 1,
        "task_id": "task-1-xxx",
        "message": "Match created and question generation started"
    }
    """
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        }, status=400)
    
    difficulty = data.get('difficulty', 'medium')
    ai_mode = data.get('ai_mode', 'random')
    num_rounds = int(data.get('num_rounds', 5))
    
    try:
        from .models import Match, Round, Question
        
        # Create match
        match = Match.objects.create(
            user=request.user,
            ai_mode=ai_mode,
            ai_difficulty=difficulty
        )
        
        # Add questions from pool
        questions = Question.objects.order_by('?')[:num_rounds]
        for q in questions:
            Round.objects.create(match=match, question=q)
        
        # Request AI-generated question for next round
        result = generate_ai_question_async(request.user, difficulty)
        
        response_data = {
            "success": True,
            "match_id": match.id,
            "ai_mode": ai_mode,
            "difficulty": difficulty,
            "num_rounds": num_rounds,
        }
        
        if result['success']:
            response_data.update({
                "task_id": result['task_id'],
                "question_generation": "started",
                "message": "Match created. Additional AI question being generated."
            })
        else:
            response_data.update({
                "question_generation": "failed",
                "message": "Match created but question generation failed."
            })
        
        return JsonResponse(response_data, status=201)
    
    except Exception as e:
        logger.error(f"Error creating match: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def receive_generated_question(request):
    """
    Webhook endpoint: Nhận câu hỏi từ AI Worker
    (Gọi từ question_generator /api/ai/receive/)
    
    POST /user-vs-ai/api/receive-question/
    
    Request:
    {
        "worker_task_id": "task-xyz",
        "user_id": 1,
        "questions": [...]
    }
    """
    
    try:
        token = request.headers.get("X-AI-Worker-Token")
        from django.conf import settings
        if token != settings.AI_WORKER_TOKEN:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        
        data = json.loads(request.body)
        questions = data.get('questions', [])
        
        if not questions:
            return JsonResponse({
                "success": False,
                "error": "No questions provided"
            }, status=400)
        
        logger.info(f"Received {len(questions)} questions from AI Worker")
        
        # The questions are already saved by question_generator/receive_ai_questions
        # Here you can do additional processing if needed
        
        return JsonResponse({
            "success": True,
            "message": f"Received {len(questions)} questions"
        }, status=200)
    
    except Exception as e:
        logger.error(f"Error receiving question: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
