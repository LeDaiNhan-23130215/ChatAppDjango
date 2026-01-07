from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Match, Round, Question
from .ai_model import get_ai

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

        # Lấy 5 câu hỏi đầu tiên (hoặc random nếu muốn)
        questions = Question.objects.all()[:5]

        for q in questions:
            Round.objects.create(
                match=match,
                question=q
            )

        # Redirect tới round đầu tiên
        return redirect(
            'quiz_ai_battle:play_ground',
            match_id=match.id,
            round_index=0
        )

    return render(request, "quiz_ai_battle/start.html")

# =========================
# Chơi từng round
# =========================
@login_required
def play_ground(request, match_id, round_index):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    rounds = Round.objects.filter(match=match).order_by('id')

    # Nếu round_index vượt quá số round → summary
    if round_index >= rounds.count():
        return redirect('quiz_ai_battle:summary', match_id=match.id)
    
    current_round = rounds[round_index]

    # Nếu đã trả lời → redirect
    if request.method == "POST":
        if current_round.user_answer:
            return redirect(
                "quiz_ai_battle:play_ground",
                match_id=match.id,
                round_index=round_index
            )

        # Lấy answer user
        user_ans = request.POST.get("answer")
        current_round.user_answer = user_ans
        current_round.user_correct = (user_ans == current_round.question.correct_answer)
        if current_round.user_correct:
            match.user_score += 1

        # AI trả lời
        ai = get_ai(match.ai_mode, match.ai_difficulty)
        ai_ans = ai.get_answer(current_round.question)
        current_round.ai_answer = ai_ans
        current_round.ai_correct = (ai_ans == current_round.question.correct_answer)
        if current_round.ai_correct:
            match.ai_score += 1

        # Lưu dữ liệu
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

    # Nếu chưa trả lời → quay lại play
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

    return render(request, 'quiz_ai_battle/summary.html', {
        'match': match,
        'rounds': rounds
    })
