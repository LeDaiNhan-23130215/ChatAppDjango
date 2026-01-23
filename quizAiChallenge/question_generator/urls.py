from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    # Generate quiz
    path('generate/', views.request_ai_questions, name='request_ai_questions'),
    
    # Receive results from AI worker
    path('receive/', csrf_exempt(views.receive_ai_questions), name='receive_ai_questions'),
    
    # Task tracking
    path('tasks/<str:task_id>/', views.get_task_status, name='get_task_status'),
    path('tasks/', views.list_user_tasks, name='list_user_tasks'),
]