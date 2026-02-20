"""User/auth routes — mirrors CompareGPT pattern."""

from fastapi import APIRouter, Header
from typing import Optional

from backend.db.schemas import ValidateRequest, ValidateResponse, LogoutResponse
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/api/user", tags=["User"])


@router.post("/validate", response_model=ValidateResponse)
async def validate(
    request: ValidateRequest,
    authorization: Optional[str] = Header(None),
):
    if request.sso_token:
        result = await auth_service.exchange_sso_token(request.sso_token)
        return ValidateResponse(**result)

    if authorization and authorization.startswith("Bearer "):
        result = await auth_service.validate_access_token(authorization)
        return ValidateResponse(**result)

    return ValidateResponse(success=False, valid=False, message="Missing credentials")


@router.post("/logout", response_model=LogoutResponse)
async def logout():
    return LogoutResponse(success=True)
