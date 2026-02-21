"""Target CRUD routes — the core of the targeting system."""

from fastapi import APIRouter, Header, HTTPException, Query
from typing import Optional

from backend.db.schemas import (
    TargetCreate, TargetUpdate, TargetResponse,
    TargetListResponse,
)
from backend.db.repo import repo
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/api/targets", tags=["Targets"])

DEFAULT_USER_ID = 1


def _get_user_id(authorization: Optional[str]) -> int:
    """Extract user from token, fall back to default user for demo."""
    if authorization:
        user = auth_service.extract_user(authorization)
        if user:
            return user["user_id"]
    return DEFAULT_USER_ID


@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(
    body: TargetCreate,
    authorization: Optional[str] = Header(None),
):
    uid = _get_user_id(authorization)
    data = body.model_dump()
    target = repo.create_target(uid, data)
    repo.log_event(uid, target["id"], "target.created", {"title": target["title"]})
    return TargetResponse(**target)


@router.get("", response_model=TargetListResponse)
async def list_targets(
    authorization: Optional[str] = Header(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    uid = _get_user_id(authorization)
    targets, total = repo.list_targets(uid, status=status, limit=limit, offset=offset)
    return TargetListResponse(targets=targets, total=total)


@router.get("/maturity-summary")
async def maturity_summary(authorization: Optional[str] = Header(None)):
    uid = _get_user_id(authorization)
    summary = repo.get_maturity_summary(uid)
    return {"success": True, "summary": summary}


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    authorization: Optional[str] = Header(None),
):
    target = repo.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return TargetResponse(**target)


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    body: TargetUpdate,
    authorization: Optional[str] = Header(None),
):
    uid = _get_user_id(authorization)
    existing = repo.get_target(target_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Target not found")

    updates = body.model_dump(exclude_none=True)
    target = repo.update_target(target_id, updates)
    repo.log_event(uid, target_id, "target.updated", updates)
    return TargetResponse(**target)


@router.delete("/{target_id}")
async def delete_target(
    target_id: int,
    authorization: Optional[str] = Header(None),
):
    uid = _get_user_id(authorization)
    existing = repo.get_target(target_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Target not found")
    repo.delete_target(target_id)
    repo.log_event(uid, target_id, "target.deleted")
    return {"success": True}
