from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from learning_path.models import LearningPath
from entrance_test.models import EntranceTestResult
from leaderboard.services import get_top_users
# Create your views here.
@login_required
def homepage(request):
    """Trang chủ chính của web"""
    user = request.user

    path = (
        LearningPath.objects.filter(user=user, is_active=True)
        .order_by('-created_at')
        .prefetch_related('items')
        .first()
    )

    top_users = get_top_users(3)

    context = {
        "path": path,
        "progress": path.get_progress_percent() if path else 0,
        "top_users": top_users,
    }
    return render(request, "core/home.html", context)
