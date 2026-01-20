from django.urls import path
from user_profile.views import profile_view

app_name = 'profile'

urlpatterns = [
    path('', profile_view, name='profile'),
]