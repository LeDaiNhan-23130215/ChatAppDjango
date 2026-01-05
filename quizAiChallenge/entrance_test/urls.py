from django.urls import path
from . import views

app_name = "entrance_test"

urlpatterns = [
    path('intro/', views.intro_view, name='intro'),
    path('entrance-test/', views.entrance_test_view, name='entrance-test'),
    path('result/', views.result_view, name='result'),
]