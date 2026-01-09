import json, random, time
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import Minigame, GameSession, Attempt, Vocabulary, Choice
from .services.choose_meaning import build_question

# Create your views here.
@login_required
def play_choose_meaning(req):
    return render(req, 'minigames/choose_meaning.html')

@require_http_methods(["POST"])
@login_required
def create_session(req):
    user = req.user
    data = json.loads(req.body or "{}")

    minigame = Minigame.objects.get(code="choose_meaning")

    session = GameSession.objects.create(
        user=user,
        minigame=minigame,
        total_questions=data.get("total_questions", 10)
    )

    return JsonResponse({"session_id": session.id})

@require_http_methods(["GET"])
@login_required
def next_question(req, session_id):
    session = GameSession.objects.get(id=session_id)

    # Lấy vocab chưa hỏi
    asked_vocab_ids = (
        Attempt.objects
        .filter(session=session)
        .values_list("question__vocabulary_id", flat=True)
    )

    qs = Vocabulary.objects.exclude(id__in=asked_vocab_ids)

    if not qs.exists():
        return HttpResponseBadRequest("No more questions")

    vocab = random.choice(list(qs))

    # Tạo câu hỏi THẬT
    question, choices = build_question(vocab, session.minigame)

    # Tạo attempt (chưa trả lời)
    Attempt.objects.create(
        session=session,
        question=question
    )

    payload = {
        "question_id": question.id,
        "prompt": question.prompt,
        "choices": [
            {"id": c.id, "text": c.text}
            for c in choices
        ],
        "start_ts": int(time.time() * 1000)
    }

    return JsonResponse(payload)

@require_http_methods(["POST"])
@login_required
def submit_answer(request, session_id):
    session = GameSession.objects.get(id=session_id)
    data = json.loads(request.body or "{}")

    question_id = data.get("question_id")
    choice_id = data.get("choice_id")
    start_ts = data.get("start_ts")

    if not question_id or not choice_id:
        return HttpResponseBadRequest("Invalid payload")

    try:
        attempt = Attempt.objects.get(
            session=session,
            question_id=question_id,
            selected_choice__isnull=True
        )
    except Attempt.DoesNotExist:
        return HttpResponseBadRequest("Invalid question")

    try:
        choice = Choice.objects.get(id=choice_id)
    except Choice.DoesNotExist:
        return HttpResponseBadRequest("Invalid choice")

    is_correct = choice.is_correct
    end_ts = int(time.time() * 1000)

    attempt.selected_choice = choice
    attempt.is_correct = is_correct
    attempt.time_ms = end_ts - start_ts
    attempt.save()

    if is_correct:
        session.score += 1
        session.save(update_fields=["score"])

    return JsonResponse({
        "correct": is_correct,
        "score": session.score
    })

@require_http_methods(["POST"])
@login_required
def finish_session(request, session_id):
    session = GameSession.objects.get(id=session_id)
    session.finished_at = timezone.now()
    session.save(update_fields=["finished_at"])

    return JsonResponse({
        "score": session.score,
        "total_questions": session.total_questions,
        "accuracy": round(session.score / max(session.total_questions, 1), 2)
    })