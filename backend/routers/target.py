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


def _get_user(authorization: Optional[str]) -> dict:
    user = auth_service.extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(
    body: TargetCreate,
    authorization: Optional[str] = Header(None),
):
    user = _get_user(authorization)
    data = body.model_dump()
    target = repo.create_target(user["user_id"], data)
    repo.log_event(user["user_id"], target["id"], "target.created", {"title": target["title"]})
    return TargetResponse(**target)


@router.get("", response_model=TargetListResponse)
async def list_targets(
    authorization: Optional[str] = Header(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    user = _get_user(authorization)
    targets, total = repo.list_targets(user["user_id"], status=status, limit=limit, offset=offset)
    return TargetListResponse(targets=targets, total=total)


@router.get("/maturity-summary")
async def maturity_summary(authorization: Optional[str] = Header(None)):
    user = _get_user(authorization)
    summary = repo.get_maturity_summary(user["user_id"])
    return {"success": True, "summary": summary}


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    authorization: Optional[str] = Header(None),
):
    user = _get_user(authorization)
    target = repo.get_target(target_id)
    if not target or target["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Target not found")
    return TargetResponse(**target)


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    body: TargetUpdate,
    authorization: Optional[str] = Header(None),
):
    user = _get_user(authorization)
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Target not found")

    updates = body.model_dump(exclude_none=True)
    target = repo.update_target(target_id, updates)
    repo.log_event(user["user_id"], target_id, "target.updated", updates)
    return TargetResponse(**target)


@router.delete("/{target_id}")
async def delete_target(
    target_id: int,
    authorization: Optional[str] = Header(None),
):
    user = _get_user(authorization)
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Target not found")
    repo.delete_target(target_id)
    repo.log_event(user["user_id"], target_id, "target.deleted")
    return {"success": True}
