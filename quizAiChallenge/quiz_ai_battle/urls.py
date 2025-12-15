from django.urls import path
from . import views

app_name = "quiz_ai_battle"

urlpatterns = [
    path('start/', views.start_match, name='start_match'),
    path(
        'play/<int:match_id>/<int:round_index>/',
        views.play_ground,
        name='play_ground'
    ),
    path(
    'summary/<int:match_id>/',
    views.summary,
    name='summary'
),
]
