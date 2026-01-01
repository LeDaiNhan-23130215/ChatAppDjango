from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .services import cal_result, analyze_weak_parts, get_part_display, generate_learning_path
from .models import EntranceTest, EntranceTestResult, Question
from collections import defaultdict
# Create your views here.

User = get_user_model()

@login_required
def intro_view(req):
    test = EntranceTest.objects.get(title="TOEIC Entrance Test")
    questions_count = Question.objects.filter(test=test).count()
    return render(req, 'entrance_test/intro.html', {
        'questions_count': questions_count
    })

@login_required
def entrance_test_view(req):
    test = EntranceTest.objects.get(title="TOEIC Entrance Test")
    questions = Question.objects.filter(test=test).order_by('part', 'id')

    return render(req, 'entrance_test/test.html', {'questions': questions})

@login_required
def result_view(req):
    result = EntranceTestResult.objects.filter(
        user=req.user
    ).order_by('-taken_at').first()

    if not result:
        return redirect('intro')

    # ====== THỐNG KÊ THEO PART ======
    part_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

    answers = result.answers.select_related('question', 'selected_choice')

    for ans in answers:
        part = ans.question.part
        part_stats[part]['total'] += 1
        if ans.selected_choice.is_correct:
            part_stats[part]['correct'] += 1

    part_summary = []
    for part, stats in part_stats.items():
        accuracy = round(stats['correct'] / stats['total'] * 100)
        part_summary.append({
            'part': part,
            'part_name': dict(Question.PART_CHOICES)[part],
            'correct': stats['correct'],
            'total': stats['total'],
            'accuracy': accuracy,
            'wrong_rate': 100 - accuracy
        })

    context = {
        'score': result.score,
        'level': result.level,
        'correct_answers': result.correct_answers,
        'total_questions': result.total_questions,
        'part_summary': part_summary,
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

