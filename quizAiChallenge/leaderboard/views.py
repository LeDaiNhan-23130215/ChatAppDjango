from django.shortcuts import render
from .models import UserElo
from learning_path.services.progress_service import get_learning_progress
# Create your views here.
def leaderboard_view(req):
    leaderboard = []

    top_users = (
        UserElo.objects.select_related("user").order_by("-elo")[:10]
    )

    for item in top_users:
        progress = get_learning_progress(item.user)
        leaderboard.append({
            "user": item.user,
            "elo": item.elo,
            "progress": progress
        })

    return render(req, "leaderboard/leaderboard.html", {
        "leaderboard": leaderboard
    })