from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from learning_path.models import LearningPath
from entrance_test.models import EntranceTestResult
from leaderboard.services import get_top_users
# Create your views here.
def public_home(request):
    return render(request, "core/public_home.html")

@login_required
def homepage(request):
    user = request.user

    path = (
        LearningPath.objects.filter(user=user, is_active=True)
        .order_by('-created_at')
        .prefetch_related('items')
        .first()
    )

    context = {
        "path": path,
        "progress": path.get_progress_percent() if path else 0,
        "top_users": get_top_users(3),
    }

    return render(request, "core/home.html", context)

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    return redirect('public-home')
