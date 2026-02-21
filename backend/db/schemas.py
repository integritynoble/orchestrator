"""Pydantic request/response schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator


# ---------- Auth ----------
class ValidateRequest(BaseModel):
    sso_token: Optional[str] = None


class ValidateResponse(BaseModel):
    success: bool = True
    valid: Optional[bool] = None
    access_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = ""


# ---------- Target ----------
class BenchmarkCreate(BaseModel):
    name: str
    metric_type: str = "score"
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None


class BenchmarkResponse(BaseModel):
    id: int
    name: str
    metric_type: str
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    recorded_at: Optional[str] = None


class BenchmarkUpdate(BaseModel):
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    name: Optional[str] = None


class BenchmarkHistoryEntry(BaseModel):
    id: int
    benchmark_id: int
    value: float
    recorded_at: Optional[str] = None


class ResourceCreate(BaseModel):
    resource_type: str
    allocated: float = 0
    unit: Optional[str] = None
    alert_at: Optional[float] = None
    hard_limit: Optional[float] = None


class ResourceResponse(BaseModel):
    id: int
    resource_type: str
    allocated: float
    consumed: float
    unit: Optional[str] = None
    alert_at: Optional[float] = None
    hard_limit: Optional[float] = None


class ResourceUpdate(BaseModel):
    consumed: Optional[float] = None
    allocated: Optional[float] = None
    alert_at: Optional[float] = None
    hard_limit: Optional[float] = None


VALID_PRIORITIES = {"critical", "high", "medium", "low"}
VALID_STATUSES = {"active", "paused", "completed", "archived"}


class TargetCreate(BaseModel):
    title: str
    description: Optional[str] = None
    domain: Optional[str] = None
    maturity_level: int = 0
    priority: str = "medium"
    benchmark_definition: Optional[str] = None
    success_criteria: Optional[str] = None
    target_score: Optional[float] = None
    tags: List[str] = []
    benchmarks: List[BenchmarkCreate] = []
    resources: List[ResourceCreate] = []

    @field_validator("maturity_level")
    @classmethod
    def validate_maturity(cls, v: int) -> int:
        if not 0 <= v <= 5:
            raise ValueError("maturity_level must be 0-5")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}")
        return v


class TargetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    maturity_level: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    benchmark_definition: Optional[str] = None
    success_criteria: Optional[str] = None
    current_score: Optional[float] = None
    target_score: Optional[float] = None
    tags: Optional[List[str]] = None

    @field_validator("maturity_level")
    @classmethod
    def validate_maturity(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 0 <= v <= 5:
            raise ValueError("maturity_level must be 0-5")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}")
        return v


class TargetResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    domain: Optional[str] = None
    maturity_level: int
    status: str
    priority: str
    benchmark_definition: Optional[str] = None
    success_criteria: Optional[str] = None
    current_score: Optional[float] = None
    target_score: Optional[float] = None
    tags: List[str] = []
    benchmarks: List[BenchmarkResponse] = []
    resources: List[ResourceResponse] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TargetListResponse(BaseModel):
    success: bool = True
    targets: List[TargetResponse] = []
    total: int = 0


# ---------- Pipeline ----------
class MaturityTransitionResponse(BaseModel):
    success: bool
    target_id: int
    from_level: int
    to_level: int
    message: str


class PipelineSummaryResponse(BaseModel):
    success: bool = True
    summary: Dict[str, int] = {}
    total_active: int = 0
    avg_maturity: float = 0
    bottlenecks: List[Dict[str, Any]] = []
    velocity: List[Dict[str, Any]] = []


# ---------- Audit ----------
class AuditEventResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    target_id: Optional[int] = None
    event_type: str
    details: Optional[Dict[str, Any]] = None
    event_hash: Optional[str] = None
    created_at: Optional[str] = None


class AuditListResponse(BaseModel):
    success: bool = True
    events: List[AuditEventResponse] = []
    total: int = 0


# ---------- System ----------
class SystemStatusResponse(BaseModel):
    status: str
    version: str
    maintenance: bool = False
    maintenance_message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    database: str = "connected"
