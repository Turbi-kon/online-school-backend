from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.conf import settings
import jwt

@database_sync_to_async
def get_user_from_token(token):
    try:
        User = get_user_model()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return User.objects.get(id=payload["user_id"])
    except Exception as e:
        print("Ошибка при получении пользователя из токена:", e)
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]
        scope["user"] = await get_user_from_token(token)
        return await super().__call__(scope, receive, send)
