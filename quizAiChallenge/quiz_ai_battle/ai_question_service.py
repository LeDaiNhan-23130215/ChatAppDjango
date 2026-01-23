"""
Service để tạo câu hỏi từ question_generator
Integrated với quiz_ai_battle app

Sử dụng:
from quiz_ai_battle.services import generate_ai_question
question = generate_ai_question(user=request.user, difficulty='advanced')
"""

import requests
import json
import logging
import random
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def build_ai_question_payload(user, difficulty='advanced', quiz_size=1):
    """
    Build payload để request từ AI Worker
    
    Args:
        user: User object
        difficulty: 'easy', 'medium', 'hard', 'advanced'
        quiz_size: Số câu hỏi (default=1)
    
    Returns:
        dict: Payload cho AI Worker
    """
    
    # Map difficulty to level
    difficulty_to_level = {
        'easy': 'Elementary',
        'medium': 'Intermediate',
        'hard': 'Upper-intermediate',
        'advanced': 'Advanced',
    }
    
    declared_level = difficulty_to_level.get(difficulty, 'Intermediate')
    
    # Lấy thông tin user
    user_declared_level = user.declared_level or 'Intermediate'
    user_goals = user.goals or 'job'
    user_profession = user.profession or 'engineer'
    user_hobby = user.hobby or ''
    user_motivation = user.motivation_level or 5
    user_study_freq = user.referred_frequency or 'daily'
    
    # Topics mặc định (có thể customize)
    default_topics = [
        "cloud computing",
        "API design and integration",
        "debugging and error handling",
        "agile and scrum methodologies",
        "system security and best practices",
        "databases and SQL optimization",
        "code review processes",
        "CI/CD pipelines",
        "microservices architecture",
        "technical documentation",
    ]
    
    # Weak skills mặc định
    default_weak_skills = [
        "subjunctive mood in formal requests",
        "gerunds vs infinitives",
        "prepositions in technical contexts",
        "past perfect tense in bug reporting",
        "phrasal verbs in IT contexts",
        "technical vocabulary",
    ]
    
    payload = {
        "user_id": user.id,
        "quiz_size": quiz_size,
        "declared_level": declared_level,
        "english_level": declared_level,
        "goals": user_goals,
        "goal": user_goals,
        "profession": user_profession,
        "job_role": user_profession,
        "referred_frequency": user_study_freq,
        "study_frequency": user_study_freq,
        "motivation_level": str(user_motivation),
        "hobby": user_hobby or "professional development",
        "preferred_topics": random.sample(default_topics, min(5, len(default_topics))),
        "weak_skills": random.sample(default_weak_skills, min(3, len(default_weak_skills))),
        "extra_instructions": (
            f"Generate questions for user with level '{declared_level}' "
            f"in profession '{user_profession}'. "
            f"Focus on realistic workplace scenarios. "
            f"Avoid overly basic questions. "
            f"Keep difficulty at {difficulty} level. "
            f"Strictly related to IT/CS contexts."
        )
    }
    
    return payload


def generate_ai_question_async(user, difficulty='advanced'):
    """
    Gửi request tới AI Worker để tạo câu hỏi
    
    Args:
        user: User object
        difficulty: 'easy', 'medium', 'hard', 'advanced'
    
    Returns:
        dict: {
            'success': bool,
            'task_id': str (nếu thành công),
            'error': str (nếu thất bại),
            'message': str
        }
    """
    
    payload = build_ai_question_payload(user, difficulty, quiz_size=1)
    
    headers = {
        "Content-Type": "application/json",
        "X-AI-Worker-Token": settings.AI_WORKER_TOKEN
    }
    
    try:
        logger.info(f"Requesting AI question for user {user.username} (difficulty: {difficulty})")
        
        response = requests.post(
            f"{settings.AI_WORKER_URL}/generate",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 202:
            data = response.json()
            task_id = data.get("task_id")
            logger.info(f"AI question task created: {task_id}")
            
            return {
                'success': True,
                'task_id': task_id,
                'message': 'Question generation started',
                'estimated_time': '3-10 minutes'
            }
        else:
            error_msg = f"AI Worker error: {response.status_code}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'message': 'Failed to request question generation'
            }
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout to AI Worker"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'message': 'Timeout: AI Worker is not responding'
        }
    
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'message': 'Failed to generate question'
        }


def get_question_from_task(task_id, user):
    """
    Polling: Check task status và get question khi hoàn tất
    
    Args:
        task_id: Task ID từ AI Worker
        user: User object
    
    Returns:
        dict: {
            'success': bool,
            'status': 'queued' | 'processing' | 'completed' | 'failed',
            'question': Question object (nếu completed),
            'message': str
        }
    """
    
    try:
        # Check status từ Django task tracking endpoint
        response = requests.get(
            f"{settings.BASE_URL}/api/ai/tasks/{task_id}/",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            
            if status == 'completed':
                questions_created = data.get('questions_created', 0)
                if questions_created > 0:
                    # Get the latest question for this user
                    from quiz.models import Question
                    question = Question.objects.filter(
                        id__gte=(Question.objects.count() - questions_created)
                    ).first()
                    
                    return {
                        'success': True,
                        'status': 'completed',
                        'question': question,
                        'message': f'Question generated successfully'
                    }
            
            return {
                'success': True,
                'status': status,
                'question': None,
                'message': f'Task status: {status}'
            }
        
        else:
            return {
                'success': False,
                'status': 'error',
                'question': None,
                'message': f'Error checking task status: {response.status_code}'
            }
    
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        return {
            'success': False,
            'status': 'error',
            'question': None,
            'message': f'Error: {str(e)}'
        }


def generate_question_sync_or_fallback(user, difficulty='advanced'):
    """
    Try async generation, fallback to random existing question
    
    Args:
        user: User object
        difficulty: 'easy', 'medium', 'hard', 'advanced'
    
    Returns:
        Question object or None
    """
    
    # Try AI Worker
    result = generate_ai_question_async(user, difficulty)
    
    if result['success']:
        task_id = result['task_id']
        logger.info(f"Question generation started. Task: {task_id}")
        
        # For immediate response, return random fallback
        # In production, you'd poll this task_id later
        from quiz_ai_battle.models import Question
        question = Question.objects.order_by('?').first()
        return question
    
    else:
        logger.warning(f"AI generation failed, using fallback: {result['error']}")
        # Fallback: return random existing question
        from quiz_ai_battle.models import Question
        question = Question.objects.order_by('?').first()
        return question
