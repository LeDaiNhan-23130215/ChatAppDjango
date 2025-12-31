from django.urls import path
from . import views

urlpatterns = [
    path('intro/', views.intro_view, name='intro'),
    path('entrance-test/', views.entrance_test_view, name='entrance-test'),
    path('result/', views.result_view, name='result'),
    path('learning-path/', views.learning_path_view, name='learning-path'),
]