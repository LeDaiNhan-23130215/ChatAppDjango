from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Match, Round, Question
# Create your views here.
# @login_required
def start_match(request):
    user = request.user if request.user.is_authenticated else None

    match = Match.objects.create(user = user)

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

# @login_required
def play_ground(request, match_id, round_index):
    match = get_object_or_404(Match, id=match_id)
    rounds = Round.objects.filter(match = match).order_by('id')

    if round_index >= rounds.count():
        return redirect('quiz_ai_battle:summary', match_id = match.id)
    
    current_round = rounds[round_index]

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