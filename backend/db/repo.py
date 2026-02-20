"""Data access layer."""

from contextlib import contextmanager
from typing import Optional, List
from sqlalchemy.orm import joinedload

from backend.db.models import (
    SessionLocal, UserModel, TargetModel, BenchmarkModel,
    ResourceModel, AuditEventModel,
)


class Repository:
    @contextmanager
    def get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ---- Users ----
    def upsert_user(self, user_data: dict, sso_token: str) -> dict:
        user_info = user_data.get("user_info", {})
        uid = user_info.get("user_id")
        with self.get_db() as db:
            user = db.query(UserModel).filter(UserModel.user_id == uid).first()
            if user:
                user.sso_token = sso_token
                user.user_name = user_info.get("user_name", user.user_name)
            else:
                user = UserModel(
                    user_id=uid,
                    user_name=user_info.get("user_name"),
                    email=user_info.get("email"),
                    sso_token=sso_token,
                    api_key=user_data.get("api_key"),
                )
                db.add(user)
            db.commit()
            db.refresh(user)
            return {"user_id": user.user_id, "user_name": user.user_name, "email": user.email, "role": user.role}

    def get_user(self, user_id: int) -> Optional[dict]:
        with self.get_db() as db:
            u = db.query(UserModel).filter(UserModel.user_id == user_id).first()
            if not u:
                return None
            return {"user_id": u.user_id, "user_name": u.user_name, "email": u.email, "role": u.role, "api_key": u.api_key}

    # ---- Targets ----
    def create_target(self, user_id: int, data: dict) -> TargetModel:
        with self.get_db() as db:
            benchmarks_data = data.pop("benchmarks", [])
            resources_data = data.pop("resources", [])

            target = TargetModel(user_id=user_id, **data)
            db.add(target)
            db.flush()

            for b in benchmarks_data:
                db.add(BenchmarkModel(target_id=target.id, **b))
            for r in resources_data:
                db.add(ResourceModel(target_id=target.id, **r))

            db.commit()
            db.refresh(target)
            return self._target_to_dict(db, target)

    def get_target(self, target_id: int) -> Optional[dict]:
        with self.get_db() as db:
            t = db.query(TargetModel).options(
                joinedload(TargetModel.benchmarks),
                joinedload(TargetModel.resources),
            ).filter(TargetModel.id == target_id).first()
            if not t:
                return None
            return self._target_to_dict(db, t)

    def list_targets(self, user_id: int, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> tuple:
        with self.get_db() as db:
            q = db.query(TargetModel).filter(TargetModel.user_id == user_id)
            if status:
                q = q.filter(TargetModel.status == status)
            total = q.count()
            targets = q.options(
                joinedload(TargetModel.benchmarks),
                joinedload(TargetModel.resources),
            ).order_by(TargetModel.updated_at.desc()).offset(offset).limit(limit).all()
            return [self._target_to_dict(db, t) for t in targets], total

    def update_target(self, target_id: int, data: dict) -> Optional[dict]:
        with self.get_db() as db:
            t = db.query(TargetModel).filter(TargetModel.id == target_id).first()
            if not t:
                return None
            for k, v in data.items():
                if v is not None and hasattr(t, k):
                    setattr(t, k, v)
            db.commit()
            db.refresh(t)
            return self._target_to_dict(db, t)

    def delete_target(self, target_id: int) -> bool:
        with self.get_db() as db:
            t = db.query(TargetModel).filter(TargetModel.id == target_id).first()
            if not t:
                return False
            db.delete(t)
            db.commit()
            return True

    def get_maturity_summary(self, user_id: int) -> dict:
        with self.get_db() as db:
            targets = db.query(TargetModel).filter(
                TargetModel.user_id == user_id,
                TargetModel.status == "active",
            ).all()
            summary = {i: 0 for i in range(6)}
            for t in targets:
                lvl = t.maturity_level
                if 0 <= lvl <= 5:
                    summary[lvl] += 1
            return summary

    # ---- Audit ----
    def log_event(self, user_id: int, target_id: Optional[int], event_type: str, details: dict = None):
        with self.get_db() as db:
            evt = AuditEventModel(
                user_id=user_id,
                target_id=target_id,
                event_type=event_type,
                details=details or {},
            )
            db.add(evt)
            db.commit()

    # ---- Helpers ----
    def _target_to_dict(self, db, t: TargetModel) -> dict:
        return {
            "id": t.id,
            "user_id": t.user_id,
            "title": t.title,
            "description": t.description,
            "domain": t.domain,
            "maturity_level": t.maturity_level,
            "status": t.status,
            "priority": t.priority,
            "benchmark_definition": t.benchmark_definition,
            "success_criteria": t.success_criteria,
            "current_score": t.current_score,
            "target_score": t.target_score,
            "tags": t.tags or [],
            "benchmarks": [
                {
                    "id": b.id,
                    "name": b.name,
                    "metric_type": b.metric_type,
                    "current_value": b.current_value,
                    "target_value": b.target_value,
                    "unit": b.unit,
                    "recorded_at": str(b.recorded_at) if b.recorded_at else None,
                }
                for b in (t.benchmarks or [])
            ],
            "resources": [
                {
                    "id": r.id,
                    "resource_type": r.resource_type,
                    "allocated": r.allocated,
                    "consumed": r.consumed,
                    "unit": r.unit,
                }
                for r in (t.resources or [])
            ],
            "created_at": str(t.created_at) if t.created_at else None,
            "updated_at": str(t.updated_at) if t.updated_at else None,
        }


repo = Repository()
