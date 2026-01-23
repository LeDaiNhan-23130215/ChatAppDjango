"""
EXAMPLE: Complete Integration of AI Question Generation into Quiz AI Battle

This file shows how to modify existing views to integrate AI question generation.
Copy and paste relevant code into your actual views.py file.
"""

# ============================================================================
# OPTION 1: Minimal Integration (Simplest)
# ============================================================================

# In quiz_ai_battle/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Match, Round
from quiz.models import Question
from .ai_question_service import generate_ai_question_async
import logging

logger = logging.getLogger(__name__)

@login_required
def start_match_minimal(request):
    """
    Create match with existing questions + trigger AI question generation.
    Simplest integration - all synchronous.
    """
    
    user = request.user
    difficulty = request.POST.get('difficulty', 'medium')
    ai_mode = request.POST.get('ai_mode', 'random')
    num_rounds = int(request.POST.get('num_rounds', 10))
    
    # Step 1: Create match with existing questions
    match = Match.objects.create(
        user=user,
        ai_mode=ai_mode,
        ai_difficulty=difficulty
    )
    
    # Step 2: Get existing questions for initial rounds
    existing_questions = Question.objects.filter(
        difficulty=difficulty
    ).order_by('?')[:num_rounds]
    
    if existing_questions.count() < num_rounds:
        logger.warning(f"Not enough questions for difficulty {difficulty}")
    
    # Step 3: Create rounds with existing questions
    for i, question in enumerate(existing_questions):
        Round.objects.create(
            match=match,
            question=question,
            round_number=i + 1
        )
    
    # ➕ Step 4 (NEW): Generate AI question in background
    try:
        result = generate_ai_question_async(
            user=user,
            difficulty=difficulty
        )
        
        if result['success']:
            match.ai_question_task_id = result['task_id']
            match.ai_question_status = 'processing'
            match.save()
            logger.info(f"AI question generation started: {result['task_id']}")
        else:
            logger.error(f"AI question generation failed: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"Error generating AI question: {str(e)}")
    
    return redirect('quiz_ai_battle:play_ground', match_id=match.id)


# ============================================================================
# OPTION 2: Advanced Integration (With Status Tracking)
# ============================================================================

@login_required
def start_match_advanced(request):
    """
    Create match + trigger AI generation + track status.
    More robust with error handling.
    """
    
    user = request.user
    difficulty = request.POST.get('difficulty', 'medium')
    ai_mode = request.POST.get('ai_mode', 'random')
    num_rounds = int(request.POST.get('num_rounds', 10))
    
    try:
        # Create match
        match = Match.objects.create(
            user=user,
            ai_mode=ai_mode,
            ai_difficulty=difficulty,
            ai_question_task_id=None,
            ai_question_status='not_started'
        )
        
        # Add existing questions
        questions = Question.objects.filter(
            difficulty=difficulty
        ).order_by('?')[:num_rounds]
        
        for i, question in enumerate(questions):
            Round.objects.create(
                match=match,
                question=question,
                round_number=i + 1
            )
        
        # Trigger AI question generation
        from .ai_question_service import generate_ai_question_async
        
        result = generate_ai_question_async(
            user=user,
            difficulty=difficulty
        )
        
        if result['success']:
            match.ai_question_task_id = result['task_id']
            match.ai_question_status = 'processing'
            match.save()
            
            logger.info(
                f"Match {match.id}: AI question generation started "
                f"(task_id: {result['task_id']})"
            )
        else:
            match.ai_question_status = 'failed'
            match.save()
            
            logger.warning(
                f"Match {match.id}: AI question generation failed - "
                f"{result.get('error')}"
            )
        
        return redirect('quiz_ai_battle:play_ground', match_id=match.id)
    
    except Exception as e:
        logger.error(f"Error in start_match_advanced: {str(e)}", exc_info=True)
        return redirect('quiz_ai_battle:start')


@login_required
def check_ai_question_status(request, match_id):
    """
    AJAX endpoint to check if AI question is ready.
    """
    
    match = get_object_or_404(Match, id=match_id, user=request.user)
    
    if not match.ai_question_task_id:
        return JsonResponse({
            'success': False,
            'status': 'not_started',
            'message': 'AI question generation not started'
        })
    
    try:
        from .ai_question_service import get_question_from_task
        
        result = get_question_from_task(match.ai_question_task_id)
        
        # Update match status
        match.ai_question_status = result.get('status', 'unknown')
        match.save()
        
        return JsonResponse(result)
    
    except Exception as e:
        logger.error(f"Error checking AI question status: {str(e)}")
        
        return JsonResponse({
            'success': False,
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def add_ai_question_to_match(request, match_id, question_id):
    """
    Add a generated AI question to the match's remaining rounds.
    """
    
    match = get_object_or_404(Match, id=match_id, user=request.user)
    question = get_object_or_404(Question, id=question_id)
    
    # Find next available round number
    max_round = Round.objects.filter(match=match).aggregate(
        max_round=models.Max('round_number')
    )['max_round'] or 0
    
    # Add AI question to next rounds (round 5-9 for example)
    for i in range(5, 10):
        if not Round.objects.filter(match=match, round_number=i).exists():
            Round.objects.create(
                match=match,
                question=question,
                round_number=i
            )
            logger.info(f"Added AI question {question_id} to match {match_id} round {i}")
    
    return JsonResponse({
        'success': True,
        'message': 'AI question added to match',
        'question_id': question_id
    })


# ============================================================================
# OPTION 3: API Integration (For Frontend Calls)
# ============================================================================

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as rest_status

@api_view(['POST'])
@login_required
def api_create_match_with_ai(request):
    """
    API endpoint for frontend to create match + AI question generation.
    Frontend can call this via fetch() or axios.
    """
    
    user = request.user
    difficulty = request.data.get('difficulty', 'medium')
    ai_mode = request.data.get('ai_mode', 'random')
    num_rounds = int(request.data.get('num_rounds', 10))
    
    try:
        # Create match
        match = Match.objects.create(
            user=user,
            ai_mode=ai_mode,
            ai_difficulty=difficulty
        )
        
        # Add rounds with existing questions
        questions = Question.objects.filter(
            difficulty=difficulty
        ).order_by('?')[:num_rounds]
        
        for i, question in enumerate(questions):
            Round.objects.create(
                match=match,
                question=question,
                round_number=i + 1
            )
        
        # Start AI generation
        result = generate_ai_question_async(
            user=user,
            difficulty=difficulty
        )
        
        response_data = {
            'success': True,
            'match_id': match.id,
            'difficulty': difficulty,
            'ai_mode': ai_mode,
            'num_rounds': num_rounds,
            'initial_questions': questions.count(),
            'message': 'Match created'
        }
        
        if result['success']:
            response_data.update({
                'ai_question_task_id': result['task_id'],
                'ai_status': 'processing',
                'message': 'Match created. Generating AI questions...'
            })
        else:
            response_data.update({
                'ai_question_task_id': None,
                'ai_status': 'failed',
                'message': f"Match created but AI generation failed: {result.get('error')}"
            })
        
        return Response(response_data, status=rest_status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error creating match with AI: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=rest_status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@login_required
def api_match_ai_question_status(request, match_id):
    """
    Check if AI question is ready for a match.
    """
    
    match = get_object_or_404(Match, id=match_id, user=request.user)
    
    if not match.ai_question_task_id:
        return Response({
            'success': False,
            'status': 'not_started'
        })
    
    try:
        from .ai_question_service import get_question_from_task
        
        result = get_question_from_task(match.ai_question_task_id)
        return Response(result)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=rest_status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# OPTION 4: Template Integration (For Django Forms)
# ============================================================================

"""
In your quiz_ai_battle/templates/start_match.html:

{% extends 'base.html' %}

{% block content %}
<div class="container">
    <h1>Start AI Battle Match</h1>
    
    <form method="post" action="{% url 'quiz_ai_battle:start_match' %}" id="matchForm">
        {% csrf_token %}
        
        <div class="form-group">
            <label for="difficulty">Difficulty:</label>
            <select name="difficulty" id="difficulty" required>
                <option value="easy">Easy</option>
                <option value="medium" selected>Medium</option>
                <option value="hard">Hard</option>
                <option value="advanced">Advanced</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="ai_mode">AI Mode:</label>
            <select name="ai_mode" id="ai_mode" required>
                <option value="random">Random</option>
                <option value="adaptive">Adaptive</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="num_rounds">Number of Rounds:</label>
            <input type="number" name="num_rounds" id="num_rounds" value="10" min="5" max="20">
        </div>
        
        <div id="status" style="display:none;" class="alert alert-info">
            Generating AI questions... Please wait.
        </div>
        
        <button type="submit" class="btn btn-primary">Start Match</button>
    </form>
    
    <script>
    document.getElementById('matchForm').addEventListener('submit', function(e) {
        const status = document.getElementById('status');
        status.style.display = 'block';
        status.innerHTML = 'Creating match and generating AI questions...';
    });
    </script>
</div>
{% endblock %}
"""

# ============================================================================
# OPTION 5: Complete Match Flow with AI Integration
# ============================================================================

@login_required
def play_ground_with_ai(request, match_id):
    """
    Play a round and check if AI question is ready to add.
    """
    
    user = request.user
    match = get_object_or_404(Match, id=match_id, user=user)
    
    # Get current round
    round_number = int(request.GET.get('round', 1))
    current_round = get_object_or_404(
        Round,
        match=match,
        round_number=round_number
    )
    
    context = {
        'match': match,
        'current_round': current_round,
        'question': current_round.question,
        'round_number': round_number,
        'total_rounds': match.rounds.count()
    }
    
    # Check if AI question is ready
    if match.ai_question_task_id and match.ai_question_status == 'processing':
        try:
            from .ai_question_service import get_question_from_task
            
            result = get_question_from_task(match.ai_question_task_id)
            
            if result['status'] == 'completed':
                # AI question ready!
                ai_question = result.get('question')
                
                if ai_question:
                    # Add to remaining rounds
                    max_round = match.rounds.aggregate(
                        max=models.Max('round_number')
                    )['max'] or 0
                    
                    for i in range(max(6, max_round + 1), max_round + 6):
                        if not Round.objects.filter(match=match, round_number=i).exists():
                            Round.objects.create(
                                match=match,
                                question_id=ai_question['id'],
                                round_number=i
                            )
                    
                    # Update match
                    match.ai_question_status = 'completed'
                    match.ai_question_id = ai_question['id']
                    match.save()
                    
                    context['ai_question_added'] = True
                    context['ai_question'] = ai_question
                    
                    logger.info(f"AI question added to match {match_id}")
            
            elif result['status'] == 'failed':
                match.ai_question_status = 'failed'
                match.save()
                context['ai_question_error'] = result.get('message')
        
        except Exception as e:
            logger.error(f"Error checking AI question: {str(e)}")
            context['ai_question_error'] = str(e)
    
    return render(request, 'quiz_ai_battle/play_ground.html', context)


# ============================================================================
# OPTION 6: Settings Models (Helper Classes)
# ============================================================================

"""
Optionally, update quiz_ai_battle/models.py to add these fields to Match:

from django.db import models

class Match(models.Model):
    # ... existing fields ...
    
    # NEW: AI Question Tracking
    ai_question_task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Task ID for AI question generation"
    )
    ai_question_status = models.CharField(
        max_length=50,
        choices=[
            ('not_started', 'Not Started'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='not_started'
    )
    ai_question_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of the AI-generated question"
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Match #{self.id} - {self.user.username}"
"""

# ============================================================================
# URL CONFIGURATION
# ============================================================================

"""
In quiz_ai_battle/urls.py, add these URL patterns:

from django.urls import path
from . import views

app_name = 'quiz_ai_battle'

urlpatterns = [
    # Original patterns
    path('', views.start_match, name='start'),
    path('<int:match_id>/play/', views.play_ground, name='play_ground'),
    path('<int:match_id>/round/<int:round_id>/result/', views.round_result, name='round_result'),
    path('<int:match_id>/summary/', views.summary, name='summary'),
    
    # NEW: AI Integration patterns
    path('<int:match_id>/ai-status/', views.check_ai_question_status, name='ai_status'),
    path('<int:match_id>/add-ai-question/<int:question_id>/', views.add_ai_question_to_match, name='add_ai_question'),
    
    # NEW: API endpoints
    path('api/match/create-with-ai/', views.api_create_match_with_ai, name='api_create_match_ai'),
    path('api/match/<int:match_id>/ai-status/', views.api_match_ai_question_status, name='api_match_ai_status'),
]
"""

print("=" * 80)
print("INTEGRATION EXAMPLES LOADED")
print("=" * 80)
print("""
Choose one of 6 options:

1. Minimal Integration - Simplest, just trigger async generation
2. Advanced Integration - With status tracking and error handling  
3. API Integration - For frontend fetch() calls
4. Template Integration - For Django form-based interaction
5. Complete Flow - Full match gameplay with AI integration
6. Settings Models - Update Match model with AI tracking fields

Copy relevant code from the option you choose into your actual files.

See INTEGRATION_GUIDE.md for more detailed examples.
""")
