"""User/auth routes — exact CompareGPT pattern."""

from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from backend.db.schemas import ValidateRequest, ValidateResponse, LogoutResponse
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/api/user", tags=["User"])


@router.post("/validate", response_model=ValidateResponse)
async def validate(
    request: ValidateRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Unified validation endpoint — two modes:
    Mode 1: SSO Token Exchange  → body: { sso_token: "..." }
    Mode 2: Access Token Validate → header: Authorization: Bearer <token>
    """
    if request.sso_token:
        return await auth_service.exchange_sso_token(request.sso_token)

    if authorization and authorization.startswith("Bearer "):
        return await auth_service.validate_access_token(authorization)

    raise HTTPException(
        status_code=400,
        detail={
            "error": "missing_credentials",
            "message": "Either sso_token or Authorization header is required",
            "require_reauth": True,
        },
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(authorization: Optional[str] = Header(None)):
    return await auth_service.logout_user(authorization)
