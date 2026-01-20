import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack  # Hoặc dùng custom middleware
from quiz.middleware import TokenAuthMiddleware  # Import custom middleware nếu cần

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')

django_asgi_app = get_asgi_application()

from quiz import routing  # Import sau khi setup Django

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        # Dùng AuthMiddlewareStack cho session-based auth
        AuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        )
        # HOẶC dùng custom TokenAuthMiddleware
        # TokenAuthMiddleware(
        #     URLRouter(
        #         routing.websocket_urlpatterns
        #     )
        # )
    ),
})