"""Authentication service — SSO + JWT, following CompareGPT pattern."""

import jwt
import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.core.config import settings
from backend.db.repo import repo

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.algorithm = "HS256"

    async def exchange_sso_token(self, sso_token: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    settings.SSO_VALIDATE_URL,
                    json={"token": sso_token},
                )
                resp.raise_for_status()
                data = resp.json()

            if not data.get("valid"):
                return {"success": False, "valid": False, "message": "Invalid SSO token"}

            user_dict = repo.upsert_user(data, sso_token)
            access_token = self._generate_jwt(data)

            return {
                "success": True,
                "valid": True,
                "access_token": access_token,
                "user": {
                    "valid": True,
                    "user_info": user_dict,
                    "api_key": data.get("api_key"),
                },
            }
        except Exception as e:
            logger.error("SSO exchange failed: %s", e)
            return {"success": False, "valid": False, "message": str(e)}

    async def validate_access_token(self, auth_header: str) -> dict:
        try:
            token = auth_header.replace("Bearer ", "")
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.algorithm])
            user_info = payload.get("user_info", {})
            uid = user_info.get("user_id")
            user = repo.get_user(uid)
            if not user:
                return {"success": False, "valid": False, "message": "User not found"}
            return {
                "success": True,
                "valid": True,
                "user": {
                    "valid": True,
                    "user_info": user,
                    "api_key": user.get("api_key"),
                },
            }
        except jwt.ExpiredSignatureError:
            return {"success": False, "valid": False, "message": "Token expired"}
        except Exception as e:
            logger.error("Token validation failed: %s", e)
            return {"success": False, "valid": False, "message": str(e)}

    def _generate_jwt(self, user_data: dict) -> str:
        user_info = user_data.get("user_info", {})
        payload = {
            "user_info": user_info,
            "exp": datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=self.algorithm)

    def extract_user(self, auth_header: Optional[str]) -> Optional[dict]:
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        try:
            token = auth_header.replace("Bearer ", "")
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.algorithm])
            return payload.get("user_info")
        except Exception:
            return None


auth_service = AuthService()
