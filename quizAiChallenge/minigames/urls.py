from django.urls import path
from . import views

app_name = 'minigames'
urlpatterns = [
    path('sessions/', views.create_session, name='create_session'),
    path('sessions/<int:session_id>/next', views.next_question, name='next_question'),
    path('sessions/<int:session_id>/answer', views.submit_answer, name='submit_answer'),
    path('sessions/<int:session_id>/finish', views.finish_session, name='finish_session'),
    path('play/choose-meaning/', views.play_choose_meaning, name='play_choose_meaning'),
]
