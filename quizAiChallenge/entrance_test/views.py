from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from learning_profile.services.analyzer import analyze_entrance_test
from learning_path.services.path_generator import generate_learning_path
from .models import EntranceTest, EntranceTestResult, Question, UserAnswer, Choice
from collections import defaultdict
from django.utils import timezone
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

    if req.method == 'POST':
        correct = 0
        answers_cache = []

        # Duyệt câu trả lời
        for question in questions:
            choice_id = req.POST.get(f'q{question.id}')
            if not choice_id:
                continue

            answers_cache.append((question, choice_id))

            choice = Choice.objects.get(id=choice_id)
            if choice.is_correct:
                correct += 1

        total = len(answers_cache)
        score = round(correct / total * 100)

        # TẠO RESULT
        result = EntranceTestResult.objects.create(
            user=req.user,
            test=test,
            score=score,
            correct_answers=correct,
            total_questions=total,
            level='BEGINNER',
            taken_at=timezone.now()
        )

        # LƯU UserAnswer
        for question, choice_id in answers_cache:
            UserAnswer.objects.create(
                result=result,
                question=question,
                selected_choice_id=choice_id
            )

        # PHÂN TÍCH & SINH LEARNING PATH
        analyze_entrance_test(result)
        generate_learning_path(result)

        return redirect('result')

    return render(req, 'entrance_test/test.html', {
        'questions': questions
    })

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

