"""
ASGI config for quizAiChallenge project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import quiz.routing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(), 
    'websocket': URLRouter(quiz.routing.websocket_urlpatterns)
    })


