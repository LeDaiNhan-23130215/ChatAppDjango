from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.lobby, name='lobby'),
    path('create/', views.create_room, name='create_room'),
    path('join/', views.join_room, name='join_room'),
    path('room/<str:code>/', views.quiz_room, name='quiz_room'),
]