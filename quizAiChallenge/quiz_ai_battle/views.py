from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Match, Round, Question
from .ai_model import get_ai
# Create your views here.
# @login_required
def start_match(request):
    if request.method == "POST":
        ai_mode = request.POST.get("ai_mode", "random")

        match = Match.objects.create(
            user=request.user if request.user.is_authenticated else None,
            ai_mode=ai_mode
        )

        questions = Question.objects.all()[:5]

        for q in questions:
            Round.objects.create(
                match = match,
                question = q
            )

        return redirect(
            'quiz_ai_battle:play_ground',
            match_id = match.id,
            round_index = 0
        )
    return render(request, "quiz_ai_battle/start.html")

# @login_required
def play_ground(request, match_id, round_index):
    match = get_object_or_404(Match, id=match_id)
    rounds = Round.objects.filter(match = match).order_by('id')

    if round_index >= rounds.count():
        return redirect('quiz_ai_battle:summary', match_id = match.id)
    
    current_round = rounds[round_index]

    if request.method == "POST":

        if current_round.user_answer:
            return redirect(
                "quiz_ai_battle:play_ground",
                match_id = match.id,
                round_index = round_index
            )
        
        userAns = request.POST.get("answer")
        current_round.user_answer = userAns
        current_round.user_correct = (
            userAns == current_round.question.correct_answer
        )

        if current_round.user_correct:
            match.user_score += 1

        ai = get_ai(match.ai_mode)
        aiAns = ai.get_answer(current_round.question)
        current_round.ai_answer = aiAns
        current_round.ai_correct = (
            aiAns == current_round.question.correct_answer
        )

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

def summary(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    rounds = Round.objects.filter(match=match)

    return render(request, 'quiz_ai_battle/summary.html', {
        'match': match,
        'rounds': rounds
    })

def round_result(request, match_id, round_index):
    match = get_object_or_404(Match, id=match_id)
    rounds = Round.objects.filter(match=match).order_by("id")

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
