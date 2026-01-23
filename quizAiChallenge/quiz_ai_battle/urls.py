from django.urls import path
from . import views
from .api_views import (
    generate_question,
    check_question_status,
    create_match_with_ai_question,
    receive_generated_question,
)

app_name = "quiz_ai_battle"

urlpatterns = [
    # Original views
    path('start/', views.start_match, name='start_match'),
    path(
        'play/<int:match_id>/<int:round_index>/',
        views.play_ground,
        name='play_ground'
    ),
    path(
        "result/<int:match_id>/<int:round_index>/",
        views.round_result,
        name="round_result"
    ),
    path(
    'summary/<int:match_id>/',
    views.summary,
    name='summary'
    ),
    
    # API endpoints for AI question generation
    path('api/generate-question/', generate_question, name='api_generate_question'),
    path('api/question-status/<str:task_id>/', check_question_status, name='api_check_status'),
    path('api/create-match/', create_match_with_ai_question, name='api_create_match'),
    path('api/receive-question/', receive_generated_question, name='api_receive_question'),
]
