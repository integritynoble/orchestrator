"""SQLAlchemy ORM models for the targeting system."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from backend.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def now():
    return datetime.now(timezone.utc)


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    role = Column(String, default="user")
    sso_token = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


class TargetModel(Base):
    """An intelligence target — a specific problem/domain to solve."""
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=True)
    maturity_level = Column(Integer, default=0)  # L0-L5
    status = Column(String, default="active")  # active, paused, completed, archived
    priority = Column(String, default="medium")  # critical, high, medium, low
    benchmark_definition = Column(Text, nullable=True)
    success_criteria = Column(Text, nullable=True)
    current_score = Column(Float, nullable=True)
    target_score = Column(Float, nullable=True)
    tags = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    benchmarks = relationship("BenchmarkModel", back_populates="target", cascade="all, delete-orphan")
    resources = relationship("ResourceModel", back_populates="target", cascade="all, delete-orphan")


class BenchmarkModel(Base):
    """Benchmark measurements for a target."""
    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    metric_type = Column(String, default="score")  # score, accuracy, latency, cost
    current_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=now)

    target = relationship("TargetModel", back_populates="benchmarks")


class ResourceModel(Base):
    """Resource allocation for a target."""
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String, nullable=False)  # compute, budget, tokens, time
    allocated = Column(Float, default=0)
    consumed = Column(Float, default=0)
    unit = Column(String, nullable=True)
    updated_at = Column(DateTime, default=now, onupdate=now)

    target = relationship("TargetModel", back_populates="resources")


class AuditEventModel(Base):
    """Immutable audit log."""
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    target_id = Column(Integer, nullable=True)
    event_type = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=now)
