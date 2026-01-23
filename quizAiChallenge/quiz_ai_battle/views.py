from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Match, Round, Question
from .ai_model import get_ai
import requests
import json
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# =========================
# Bắt đầu trận đấu
# =========================
@login_required
def start_match(request):
    if request.method == "POST":
        ai_mode = request.POST.get("ai_mode", "random")
        ai_difficulty = request.POST.get("ai_difficulty", "medium")

        # Tạo match mới
        match = Match.objects.create(
            user=request.user,
            ai_mode=ai_mode,
            ai_difficulty = ai_difficulty
        )

        # Lấy 5 câu hỏi đầu tiên
        questions = Question.objects.order_by('?')[:5]

        for q in questions:
            Round.objects.create(
                match=match,
                question=q
            )

        # ✨ Trigger AI question generation in background
        try:
            _trigger_ai_question_generation(request.user, ai_difficulty)
        except Exception as e:
            logger.error(f"Failed to trigger AI generation: {str(e)}")

        return redirect(
            'quiz_ai_battle:play_ground',
            match_id=match.id,
            round_index=0
        )

    return render(request, "quiz_ai_battle/start.html")


def _trigger_ai_question_generation(user, difficulty):
    """Trigger AI question generation in background thread"""
    try:
        from question_generator.models import QuizTask
        
        ai_worker_token = getattr(settings, 'AI_WORKER_TOKEN', None)
        ai_worker_url = getattr(settings, 'AI_WORKER_URL', None)
        
        if not ai_worker_token or not ai_worker_url:
            logger.warning(f"AI Worker not configured")
            return
        
        difficulty_map = {
            'easy': 'Elementary',
            'medium': 'Intermediate',
            'hard': 'Upper-intermediate',
            'expert': 'Advanced'
        }
        
        proficiency_level = difficulty_map.get(difficulty, 'Intermediate')
        
        payload = {
            'user_id': user.id,
            'quiz_size': 1,
            'declared_level': getattr(user, 'declared_level', 'Intermediate'),
            'goals': getattr(user, 'goals', 'job'),
            'profession': getattr(user, 'profession', ''),
            'preferred_topics': [],
            'weak_skills': [],
            'extra_instructions': f'Generate 1 question with difficulty: {proficiency_level}'
        }
        
        task_id = f"task-{user.id}-{int(timezone.now().timestamp() * 1000)}"
        
        quiz_task = QuizTask.objects.create(
            task_id=task_id,
            user=user,
            quiz_size=1,
            declared_level=payload.get('declared_level'),
            goals=payload.get('goals'),
            profession=payload.get('profession'),
            preferred_topics=[],
            weak_skills=[],
            extra_instructions=payload.get('extra_instructions'),
            status='queued'
        )
        
        logger.info(f"Created QuizTask: {task_id}")
        
        import threading
        def send_to_worker():
            try:
                headers = {
                    "Content-Type": "application/json",
                    "X-AI-Worker-Token": ai_worker_token
                }
                
                response = requests.post(
                    f"{ai_worker_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 202:
                    data = response.json()
                    worker_task_id = data.get("task_id", task_id)
                    quiz_task.task_id = worker_task_id
                    quiz_task.status = 'processing'
                    quiz_task.started_at = timezone.now()
                    quiz_task.save(update_fields=['task_id', 'status', 'started_at'])
                    logger.info(f"AI generation started: {worker_task_id}")
                else:
                    quiz_task.mark_failed(f"Worker error: {response.status_code}")
                    logger.error(f"Worker error: {response.status_code}")
            except Exception as e:
                quiz_task.mark_failed(str(e))
                logger.error(f"Error: {str(e)}")
        
        thread = threading.Thread(target=send_to_worker, daemon=True)
        thread.start()
    
    except Exception as e:
        logger.error(f"Error triggering AI generation: {str(e)}")


# =========================
# Chơi từng round
# =========================
@login_required
def play_ground(request, match_id, round_index):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    rounds = Round.objects.filter(match=match).order_by('id')

    if round_index >= rounds.count():
        return redirect('quiz_ai_battle:summary', match_id=match.id)
    
    current_round = rounds[round_index]

    if request.method == "POST":
        if current_round.user_answer:
            return redirect(
                "quiz_ai_battle:play_ground",
                match_id=match.id,
                round_index=round_index
            )

        user_ans = request.POST.get("answer")
        current_round.user_answer = user_ans
        current_round.user_correct = (user_ans == current_round.question.correct_answer)
        if current_round.user_correct:
            match.user_score += 1

        ai = get_ai(match.ai_mode, match.ai_difficulty)
        ai_ans = ai.get_answer(current_round.question)
        current_round.ai_answer = ai_ans
        current_round.ai_correct = (ai_ans == current_round.question.correct_answer)
        if current_round.ai_correct:
            match.ai_score += 1

        current_round.save()
        match.save()

        return redirect(
            "quiz_ai_battle:round_result",
            match_id=match.id,
            round_index=round_index
        )

    return render(request, 'quiz_ai_battle/play.html', {
        'match': match,
        'round': current_round,
        'round_index': round_index,
        'total_rounds': rounds.count()
    })


# =========================
# Kết quả 1 round
# =========================
@login_required
def round_result(request, match_id, round_index):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    rounds = Round.objects.filter(match=match).order_by('id')

    if round_index >= rounds.count():
        return redirect("quiz_ai_battle:summary", match_id=match.id)

    current_round = rounds[round_index]

    if not current_round.user_answer:
        return redirect(
            "quiz_ai_battle:play_ground",
            match_id=match.id,
            round_index=round_index
        )

    return render(request, "quiz_ai_battle/result.html", {
        "match": match,
        "round": current_round,
        "round_index": round_index,
        "total_rounds": rounds.count()
    })


# =========================
# Summary trận đấu
# =========================
@login_required
def summary(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    rounds = Round.objects.filter(match=match)

    # ✨ NEW: Update ELO rating based on match result
    elo_change = _calculate_elo_change(match)
    if elo_change != 0:
        _update_user_elo(request.user, match, elo_change)

    return render(request, 'quiz_ai_battle/summary.html', {
        'match': match,
        'rounds': rounds
    })


def _calculate_elo_change(match):
    """Calculate ELO change based on match result"""
    result = match.result
    
    if result == 'win':
        return 30  # Win: +30 points
    elif result == 'loss':
        return -20  # Loss: -20 points
    else:
        return 0   # Draw: no change


def _update_user_elo(user, match, elo_change):
    """Update user ELO rating and record history"""
    from leaderboard.models import UserElo, EloHistory
    
    # Record history before change (use User.elo_rating as source of truth)
    elo_before = user.elo_rating
    
    # Update user profile with new ELO
    user.elo_rating += elo_change
    user.save(update_fields=['elo_rating'])
    
    # Get or create UserElo and sync
    user_elo, created = UserElo.objects.get_or_create(user=user)
    user_elo.elo = user.elo_rating
    user_elo.save(update_fields=['elo'])
    
    # Update match record
    match.elo_before = elo_before
    match.elo_after = user.elo_rating
    match.elo_change = elo_change
    match.save(update_fields=['elo_before', 'elo_after', 'elo_change'])
    
    # Record in ELO history
    EloHistory.objects.create(
        user=user,
        elo_before=elo_before,
        elo_after=user.elo_rating,
        change=elo_change
    )
