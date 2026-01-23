from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('request-quiz/', views.request_ai_questions, name='request_ai_questions'),
    path('receive/', csrf_exempt(views.receive_ai_questions), name='receive_ai_questions'),  # chỉ 'receive/'
]