from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .services import cal_result, analyze_weak_parts, get_part_display, generate_learning_path
from .models import EntranceTest, EntranceTestResult
# Create your views here.

User = get_user_model()

@login_required
def intro_view(req):
    return render(req, 'entrance_test/intro.html')

@login_required
def entrance_test_view(req):
    test = EntranceTest.objects.get(is_active=True)
    if req.method == 'POST':
        user_answers = {
            int(k[1:]): int(v)
            for k, v in req.POST.items()
            if k.startswith('q')
        }

        result = cal_result(
            user=req.user,
            test=test,
            user_answers=user_answers
        )

        return redirect('result')
    
    questions = test.questions.prefetch_related('choices')
    return render(req, 'entrance_test/test.html', {
        'questions': questions
    })

@login_required
def result_view(req):
    result = EntranceTestResult.objects.filter(
        user = req.user
    ).order_by('-taken_at').first()

    if not result:
        return redirect('intro')

    context = {
        'score': result.score,
        'level': result.level,
        'correct_answers': result.correct_answers,
        'total_questions': result.total_questions,
    }

    return render(req, 'entrance_test/result.html', context)

@login_required
def learning_path_view(request):
    result = EntranceTestResult.objects.filter(
        user=request.user
    ).order_by('-taken_at').first()

    if not result:
        return redirect('intro')

    weak_parts = analyze_weak_parts(result)
    if not weak_parts:
        weak_parts = [
            {'part': 5, 'accuracy': 100},  # Grammar luôn nên học
            {'part': 7, 'accuracy': 100},  # Reading
        ]
    learning_path = generate_learning_path(result.level, weak_parts)

    context = {
        'level': result.level,
        'learning_path': [
            {
                'part_name': get_part_display(item['part']),
                'focus': item['focus'],
                'level_strategy': item['level_strategy'],
            }
            for item in learning_path
        ]
    }

    return render(request, 'entrance_test/learning_path.html', context)

