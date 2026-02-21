"""JWT Token Manager — exact CompareGPT pattern."""

from datetime import datetime, timedelta
from typing import Optional
import jwt
import secrets

from backend.core.config import settings

ACCESS_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


class TokenManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def create_access_token(self, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),
        }
        return jwt.encode(payload, self.secret_key, algorithm=ALGORITHM)

    def verify_access_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


SECRET_KEY = getattr(settings, "SECRET_KEY", secrets.token_urlsafe(32))
token_manager = TokenManager(SECRET_KEY)
