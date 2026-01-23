from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import UserElo, EloHistory
from learning_path.services.progress_service import get_learning_progress
from quiz_ai_battle.models import Match

User = get_user_model()

# Create your views here.
def leaderboard_view(req):
    """Display ELO leaderboard"""
    leaderboard = []

    # Get top users by ELO rating
    top_users = User.objects.filter(
        elo_rating__gt=0
    ).order_by("-elo_rating")[:100]

    for rank, user in enumerate(top_users, 1):
        try:
            progress = get_learning_progress(user)
        except:
            progress = {}
        
        # Get match stats
        user_matches = Match.objects.filter(user=user)
        wins = len([m for m in user_matches if m.result == 'win'])
        losses = len([m for m in user_matches if m.result == 'loss'])
        draws = len([m for m in user_matches if m.result == 'draw'])
        total_matches = user_matches.count()
        
        leaderboard.append({
            "rank": rank,
            "user": user,
            "elo": user.elo_rating,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "total_matches": total_matches,
            "win_rate": round((wins / total_matches * 100), 2) if total_matches > 0 else 0,
            "progress": progress
        })

    return render(req, "leaderboard/leaderboard.html", {
        "leaderboard": leaderboard
    })


@login_required
def user_elo_history(request):
    """Display ELO history for logged-in user"""
    # Get user's ELO history (last 50 records)
    history = EloHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    # Get current stats
    user_matches = Match.objects.filter(user=request.user)
    wins = len([m for m in user_matches if m.result == 'win'])
    losses = len([m for m in user_matches if m.result == 'loss'])
    draws = len([m for m in user_matches if m.result == 'draw'])
    
    return render(request, 'leaderboard/user_elo_history.html', {
        'user': request.user,
        'elo_rating': request.user.elo_rating,
        'history': history,
        'stats': {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'total': wins + losses + draws,
            'win_rate': round((wins / (wins + losses + draws) * 100), 2) if (wins + losses + draws) > 0 else 0
        }
    })