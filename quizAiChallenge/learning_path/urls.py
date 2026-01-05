from django.urls import path
from learning_path.views import learning_path_view, learning_path_item_view, mock_exam_start_view, lesson_detail_view, quiz_start_view, practice_start_view, quiz_submit_view, quiz_result_view
from learning_path.views import CurrentLearningPathView

app_name = 'learning_path'

urlpatterns = [
    path('', learning_path_view, name='learning_path'),
    path('item/<int:item_id>/', learning_path_item_view, name='learning_path_item'),
    path('quiz/<int:quiz_id>/', quiz_start_view, name='quiz_start'),
    path('practice/<int:practice_id>/', practice_start_view, name='practice_start'),
    path('lesson/<int:lesson_id>/', lesson_detail_view, name='lesson_detail'),
    path('mock/<int:mock_id>/', mock_exam_start_view, name='mock_exam_start'),
    path('quiz/<int:quiz_id>/submit/', quiz_submit_view, name='quiz_submit'),
    path('quiz/<int:quiz_id>/result/', quiz_result_view, name='quiz_result'),
    path("learning-path/current/", CurrentLearningPathView.as_view(), name="current-learning-path"),
]