from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="quiz_home"),
    path("create/", views.create_room),
    path("room/<str:code>/", views.room, name="quiz_room"),
]
