from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    """
    Lấy user từ token (nếu dùng token authentication)
    Hoặc từ session (nếu dùng session authentication)
    """
    try:
        # Ví dụ với Django session
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        session = Session.objects.get(session_key=token)
        if session.expire_date < timezone.now():
            return AnonymousUser()
        
        uid = session.get_decoded().get('_auth_user_id')
        return User.objects.get(pk=uid)
    except:
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware để authenticate WebSocket connections
    """
    async def __call__(self, scope, receive, send):
        # Lấy token từ query string
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        
        # Hoặc từ headers
        headers = dict(scope.get('headers', []))
        
        # Thử lấy token từ query string
        token = params.get('token', [None])[0]
        
        # Hoặc từ cookie
        if not token:
            cookie = headers.get(b'cookie', b'').decode()
            for item in cookie.split(';'):
                if 'sessionid' in item:
                    token = item.split('=')[1].strip()
                    break
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)