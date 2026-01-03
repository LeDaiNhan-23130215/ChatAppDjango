from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from learning_path.models import LearningPath, LearningPathItem
from entrance_test.models import EntranceTestResult
from django.http import HttpResponse
from learning_path.services.progress_service import complete_item

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
def learing_path_item_view(req, item_id):
    item = get_object_or_404(
        LearningPathItem,
        id = item_id,
        path__user = req.user
    )

    if item.item_type == 'LESSON':
        return redirect('lesson_detail', item.object_id)
    if item.item_type == 'PRACTICE':
        return redirect('practice_start', item.object_id)
    if item.item_type == 'QUIZ':
        return redirect('quiz_start', item.object_id)
    if item.item_type == 'MOCK':
        return redirect('mock_exam_start', item.object_id)
    
    return render(req, "learning_path/learning_path_item.html", {
        "item": item
    })


@login_required
def lesson_detail_view(req, lesson_id):
    if req.method == 'POST':
        item_id = req.POST.get('item_id')
        item = LearningPathItem.objects.get(
            id = item_id,
            path__user = req.user
        )
    
        complete_item(item)

        return redirect('learning_path')
    return HttpResponse(f"Lesson page – lesson_id = {lesson_id}")

@login_required
def practice_start_view(req, practice_id):
    return HttpResponse(f"Practice start page – practice_id = {practice_id}")

@login_required
def quiz_start_view(req, quiz_id):
    return HttpResponse(f"Quiz start page – quiz_id = {quiz_id}")

@login_required
def quiz_submit_view(request):
    pass

@login_required
def mock_exam_start_view(req, mock_id):
    return HttpResponse(f"Mock start page – mock_id = {mock_id}")

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