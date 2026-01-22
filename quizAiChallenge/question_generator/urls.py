from django.urls import path
from . import views

urlpatterns = [
    path("generate/", views.request_ai_questions),
    path("receive/", views.receive_ai_questions),]