from django.urls import path
from . import views

app_name = 'minigames'
urlpatterns = [
    path('minigames/', views.minigames_menu, name='minigames_menu'),
    path('minigames/<str:code>/', views.play_minigame, name='play_minigame'),
    path('sessions/', views.create_session, name='create_session'),
    path('sessions/<int:session_id>/next/', views.next_question, name='next_question'),
    path('sessions/<int:session_id>/answer/', views.submit_answer, name='submit_answer'),
    path('sessions/<int:session_id>/finish/', views.finish_session, name='finish_session'),
    path('sessions/<int:session_id>/flashcard/', views.submit_flashcard, name='submit_flashcard'),
    path('sessions/<int:session_id>/summary/', views.flashcard_summary, name='flashcard_summary'),
]
