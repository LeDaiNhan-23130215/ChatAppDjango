from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from learning_path.models import LearningPath, LearningPathItem
from django.http import HttpResponse
from learning_path.services.progress_service import complete_item
# Create your views here.
@login_required
def learning_path_view(req):
    path = (
        LearningPath.objects.filter(user = req.user)
        .order_by('-created_at')
        .prefetch_related('items')
        .first()
    )
    return render(req, 'learning_path/learning_path.html', {
        'path' : path
    })

@login_required
def learing_path_item_view(req, item_id):
    item = get_object_or_404(
        LearningPathItem,
        id = item_id,
        path__user = req.user
    )

    if item.status == 'LOCKED':
        return render(req, 'learning_path/item_locked.html', {
            'item': item
        })

    if item.item_type == 'LESSON':
        return redirect('lesson_detail', item.object_id)
    if item.item_type == 'PRACTICE':
        return redirect('practice_start', item.object_id)
    if item.item_type == 'QUIZ':
        return redirect('quiz_start', item.object_id)
    if item.item_type == 'MOCK':
        return redirect('mock_exam_start', item.object_id)
    
    return redirect('learning_path')

@login_required
def lesson_detail_view(req, lesson_id):
    return HttpResponse(f"Lesson page – lesson_id = {lesson_id}")

@login_required
def practice_start_view(req, practice_id):
    return HttpResponse(f"Practice start page – practice_id = {practice_id}")

@login_required
def quiz_start_view(req, quiz_id):
    return HttpResponse(f"Quiz start page – quiz_id = {quiz_id}")

@login_required
def mock_exam_start_view(req, mock_id):
    return HttpResponse(f"Mock start page – mock_id = {mock_id}")