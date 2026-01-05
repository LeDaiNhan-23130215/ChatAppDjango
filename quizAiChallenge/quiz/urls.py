from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="quiz_home"),
    path("quiz/create/", views.create_room),
    path("quiz/room/<str:code>/", views.room, name="quiz_room"),
]
