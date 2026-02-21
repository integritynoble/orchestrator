"""Target CRUD + Pipeline + Benchmark + Resource + Audit routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from backend.db.schemas import (
    TargetCreate, TargetUpdate, TargetResponse, TargetListResponse,
    BenchmarkCreate, BenchmarkUpdate, BenchmarkResponse,
    ResourceCreate, ResourceUpdate, ResourceResponse,
    MaturityTransitionResponse, PipelineSummaryResponse,
    AuditListResponse,
)
from backend.db.repo import repo
from backend.services.auth_service import get_current_user_id

router = APIRouter(prefix="/api/targets", tags=["Targets"])


# ── Target CRUD ──────────────────────────────────────────────────────

@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(body: TargetCreate, user_id: int = Depends(get_current_user_id)):
    data = body.model_dump()
    target = repo.create_target(user_id, data)
    repo.log_event(user_id, target["id"], "target.created", {"title": target["title"]})
    return TargetResponse(**target)


@router.get("", response_model=TargetListResponse)
async def list_targets(
    user_id: int = Depends(get_current_user_id),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    targets, total = repo.list_targets(user_id, status=status, limit=limit, offset=offset)
    return TargetListResponse(targets=targets, total=total)


@router.get("/maturity-summary")
async def maturity_summary(user_id: int = Depends(get_current_user_id)):
    summary = repo.get_maturity_summary(user_id)
    return {"success": True, "summary": summary}


@router.get("/pipeline", response_model=PipelineSummaryResponse)
async def pipeline_summary(user_id: int = Depends(get_current_user_id)):
    data = repo.get_pipeline_summary(user_id)
    return PipelineSummaryResponse(**data)


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(target_id: int, user_id: int = Depends(get_current_user_id)):
    target = repo.get_target(target_id)
    if not target or target["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    return TargetResponse(**target)


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(target_id: int, body: TargetUpdate, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    updates = body.model_dump(exclude_none=True)
    target = repo.update_target(target_id, updates)
    repo.log_event(user_id, target_id, "target.updated", updates)
    return TargetResponse(**target)


@router.delete("/{target_id}")
async def delete_target(target_id: int, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    repo.delete_target(target_id)
    repo.log_event(user_id, target_id, "target.archived")
    return {"success": True}


# ── Maturity Advancement ─────────────────────────────────────────────

@router.get("/{target_id}/advance/check")
async def check_advance(target_id: int, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    return repo.check_advance_criteria(target_id)


@router.post("/{target_id}/advance", response_model=MaturityTransitionResponse)
async def advance_maturity(target_id: int, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    check = repo.check_advance_criteria(target_id)
    if not check["can_advance"]:
        raise HTTPException(status_code=400, detail=check["reason"])
    result = repo.advance_target(target_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot advance")
    repo.log_event(user_id, target_id, "maturity.advanced", result)
    return MaturityTransitionResponse(
        success=True, target_id=target_id,
        from_level=result["from_level"], to_level=result["to_level"],
        message=f"Advanced from L{result['from_level']} to L{result['to_level']}",
    )


# ── Benchmarks ───────────────────────────────────────────────────────

@router.post("/{target_id}/benchmarks", response_model=BenchmarkResponse, status_code=201)
async def add_benchmark(target_id: int, body: BenchmarkCreate, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    benchmark = repo.add_benchmark(target_id, body.model_dump())
    repo.log_event(user_id, target_id, "benchmark.added", {"name": body.name})
    return BenchmarkResponse(**benchmark)


@router.put("/{target_id}/benchmarks/{benchmark_id}", response_model=BenchmarkResponse)
async def update_benchmark(target_id: int, benchmark_id: int, body: BenchmarkUpdate, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    result = repo.update_benchmark(benchmark_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    repo.log_event(user_id, target_id, "benchmark.updated", {"benchmark_id": benchmark_id})
    return BenchmarkResponse(**result)


@router.get("/{target_id}/benchmarks/history")
async def benchmark_history(
    target_id: int, user_id: int = Depends(get_current_user_id),
    benchmark_id: Optional[int] = Query(None), limit: int = Query(100, ge=1, le=500),
):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    history = repo.get_benchmark_history(target_id, benchmark_id, limit)
    return {"success": True, "history": history}


# ── Resources ────────────────────────────────────────────────────────

@router.post("/{target_id}/resources", response_model=ResourceResponse, status_code=201)
async def add_resource(target_id: int, body: ResourceCreate, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    resource = repo.add_resource(target_id, body.model_dump())
    repo.log_event(user_id, target_id, "resource.allocated", {"type": body.resource_type, "amount": body.allocated})
    return ResourceResponse(**resource)


@router.put("/{target_id}/resources/{resource_id}")
async def update_resource(target_id: int, resource_id: int, body: ResourceUpdate, user_id: int = Depends(get_current_user_id)):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    result = repo.update_resource(resource_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    alerts = result.pop("alerts", [])
    if any(a["type"] == "budget_exceeded" for a in alerts):
        repo.update_target(target_id, {"status": "paused"})
        repo.log_event(user_id, target_id, "target.auto_paused", {"reason": "budget_exceeded"})
    repo.log_event(user_id, target_id, "resource.updated", {"resource_id": resource_id})
    return {"success": True, "resource": result, "alerts": alerts}


# ── Audit ────────────────────────────────────────────────────────────

@router.get("/{target_id}/audit", response_model=AuditListResponse)
async def target_audit(
    target_id: int, user_id: int = Depends(get_current_user_id),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
):
    existing = repo.get_target(target_id)
    if not existing or existing["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Target not found")
    events, total = repo.get_audit_events(target_id=target_id, event_type=event_type, limit=limit, offset=offset)
    return AuditListResponse(events=events, total=total)
