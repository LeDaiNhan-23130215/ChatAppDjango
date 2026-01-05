from django.urls import path
from learning_path.views import (
    learning_path_view, learning_path_item_view,
    lesson_detail_view, lesson_complete_view, lesson_result_view,
    practice_start_view, practice_submit_view, practice_result_view,
    quiz_start_view, quiz_submit_view, quiz_result_view,
    mock_exam_start_view, mock_exam_submit_view, mock_exam_result_view,
    CurrentLearningPathView
)

app_name = 'learning_path'

urlpatterns = [
    path('', learning_path_view, name='learning_path'),
    path('item/<int:item_id>/', learning_path_item_view, name='learning_path_item'),

    # Quiz
    path('quiz/<int:quiz_id>/', quiz_start_view, name='quiz_start'),
    path('quiz/<int:quiz_id>/submit/', quiz_submit_view, name='quiz_submit'),
    path('quiz/<int:quiz_id>/result/', quiz_result_view, name='quiz_result'),

    # Practice
    path('practice/<int:practice_id>/', practice_start_view, name='practice_start'),
    path('practice/<int:practice_id>/submit/', practice_submit_view, name='practice_submit'),
    path('practice/<int:practice_id>/result/', practice_result_view, name='practice_result'),

    # Lesson
    path('lesson/<int:lesson_id>/', lesson_detail_view, name='lesson_detail'),
    path('lesson/<int:lesson_id>/complete/', lesson_complete_view, name='lesson_complete'),
    path('lesson/<int:lesson_id>/result/', lesson_result_view, name='lesson_result'),

    # Mock Exam
    path('mock/<int:mock_id>/', mock_exam_start_view, name='mock_exam_start'),
    path('mock/<int:mock_id>/submit/', mock_exam_submit_view, name='mock_exam_submit'),
    path('mock/<int:mock_id>/result/', mock_exam_result_view, name='mock_exam_result'),

    # API
    path("learning-path/current/", CurrentLearningPathView.as_view(), name="current-learning-path"),
]