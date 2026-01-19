"""
URL configuration for quizAiChallenge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #Trang Admin
    path('admin/', admin.site.urls),

    # ROOT
    path('', core_views.root_redirect),

    # Public
    path('welcome/', core_views.public_home, name='public-home'),

    # Private
    path('home/', core_views.homepage, name='homepage'),

    # App accounts
    path('accounts/', include('accounts.urls')),

    # App quiz
    path('quiz/', include('quiz.urls')),  

    # App AI battle
    path('user-vs-ai/', include('quiz_ai_battle.urls')),

    #App Entrance Test
    path('entrance-test/', include('entrance_test.urls')),

    #App Learning Path
    path('api/', include('learning_path.urls')),

    #App Minigames
    path('minigames/', include('minigames.urls')),

    #App Leaderboard
    path("leaderboard/", include("leaderboard.urls")),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)