"""Pydantic request/response schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# ---------- Auth ----------
class ValidateRequest(BaseModel):
    sso_token: Optional[str] = None


class UserInfo(BaseModel):
    user_id: int
    user_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class ValidateResponse(BaseModel):
    success: bool = True
    valid: bool = True
    access_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class LogoutResponse(BaseModel):
    success: bool = True


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


class ResourceCreate(BaseModel):
    resource_type: str
    allocated: float = 0
    unit: Optional[str] = None


class ResourceResponse(BaseModel):
    id: int
    resource_type: str
    allocated: float
    consumed: float
    unit: Optional[str] = None


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


# ---------- System ----------
class SystemStatusResponse(BaseModel):
    status: str
    version: str
    maintenance: bool = False
    maintenance_message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    database: str = "connected"
