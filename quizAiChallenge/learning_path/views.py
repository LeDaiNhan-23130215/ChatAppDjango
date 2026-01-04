from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from learning_path.models import LearningPath, LearningPathItem
from entrance_test.models import EntranceTestResult
from learning_path.services.progress_service import complete_item
from quiz.models import Quiz
from lesson.models import Lesson

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from learning_path.serializers import LearningPathSerializer

# Create your views here.
@login_required
def learning_path_view(req):
    user = req.user

    if not EntranceTestResult.objects.filter(user=user).exists():
        return render(req, "learning_path/no_entrance_test.html")

    path = (
        LearningPath.objects.filter(user = req.user)
        .order_by('-created_at')
        .prefetch_related('items')
        .first()
    )
    items = path.items.all() if path else []
    return render(req, 'learning_path/learning_path.html', {
        'items': items
    })

@login_required
def learning_path_item_view(req, item_id):
    item = get_object_or_404(
        LearningPathItem,
        id=item_id,
        path__user=req.user
    )

    if item.item_type == 'LESSON':
        return redirect('learning_path:lesson_detail', lesson_id=item.object_id)
    if item.item_type == 'PRACTICE':
        return redirect('learning_path:practice_start', practice_id=item.object_id)
    if item.item_type == 'QUIZ':
        return redirect('learning_path:quiz_start', quiz_id=item.object_id)
    if item.item_type == 'MOCK':
        return redirect('learning_path:mock_exam_start', mock_id=item.object_id)
    return render(req, "learning_path/learning_path_item.html", {
        "item": item
    })

@login_required
def lesson_detail_view(req, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(req, "learning_path/lesson_detail.html", {"lesson": lesson})

@login_required
def practice_start_view(req, practice_id):
    practice = get_object_or_404(Quiz, id=practice_id, quiz_type="PRACTICE")

    return render(req, "learning_path/practice_detail.html", {
        "practice": practice
    })

@login_required
def quiz_start_view(req, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, quiz_type="QUIZ")

    return render(req, "learning_path/quiz_detail.html", {
        "quiz": quiz
    })

@login_required
def mock_exam_start_view(req, mock_id):
    mock = get_object_or_404(Quiz, id=mock_id, quiz_type="MOCK")

    return render(req, "learning_path/mock_exam_detail.html", {
        "mock": mock
    })

@login_required
def quiz_submit_view(request):
    pass

class CurrentLearningPathView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        path = LearningPath.objects.filter(
            user=user,
            is_active=True
        ).prefetch_related("items").first()

        if not path:
            return Response(
                {"detail": "No active learning path"},
                status=404
            )

        serializer = LearningPathSerializer(path)
        return Response(serializer.data)