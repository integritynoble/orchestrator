"""Data access layer."""

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import joinedload
from sqlalchemy import func

from backend.db.models import (
    SessionLocal, UserModel, TargetModel, BenchmarkModel,
    BenchmarkHistoryModel, ResourceModel, AuditEventModel,
)


class Repository:
    @contextmanager
    def get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ── Users ────────────────────────────────────────────────────────
    def upsert_user(self, user_data: dict, sso_token: str = None, api_key: str = None) -> dict:
        user_info = user_data.get("user_info", {})
        balance = user_data.get("balance", {})
        uid = user_info.get("user_id")
        if not uid:
            raise ValueError("Invalid user data: missing user_id")

        with self.get_db() as db:
            user = db.query(UserModel).filter(UserModel.user_id == uid).first()
            if user:
                if user_info.get("user_name"):
                    user.user_name = user_info["user_name"]
                if user_info.get("role"):
                    user.role = user_info["role"]
                if balance.get("credit") is not None:
                    user.credit = balance["credit"]
                if balance.get("token") is not None:
                    user.token = balance["token"]
                if sso_token is not None:
                    user.sso_token = sso_token
                if api_key is not None:
                    user.api_key = api_key
                user.updated_at = datetime.now(timezone.utc)
            else:
                user = UserModel(
                    user_id=uid,
                    user_name=user_info.get("user_name", ""),
                    email=user_info.get("email"),
                    role=user_info.get("role", "user"),
                    credit=balance.get("credit"),
                    token=balance.get("token"),
                    sso_token=sso_token,
                    api_key=api_key,
                )
                db.add(user)
            db.commit()
            db.refresh(user)
            return {
                "user_id": user.user_id,
                "user_name": user.user_name,
                "email": user.email,
                "role": user.role,
                "credit": user.credit,
                "token": user.token,
                "sso_token": user.sso_token,
                "api_key": user.api_key,
            }

    def get_user(self, user_id: int) -> Optional[dict]:
        with self.get_db() as db:
            u = db.query(UserModel).filter(UserModel.user_id == user_id).first()
            if not u:
                return None
            return {
                "user_info": {
                    "user_id": u.user_id,
                    "user_name": u.user_name,
                    "email": u.email,
                    "role": u.role,
                },
                "balance": {"credit": u.credit, "token": u.token},
                "sso_token": u.sso_token,
                "api_key": u.api_key,
            }

    def clear_user_data(self, user_id: int) -> bool:
        with self.get_db() as db:
            u = db.query(UserModel).filter(UserModel.user_id == user_id).first()
            if u:
                u.sso_token = None
                u.api_key = None
                db.commit()
                return True
            return False

    # ── Targets ──────────────────────────────────────────────────────
    def create_target(self, user_id: int, data: dict) -> dict:
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
            t.status = "archived"
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

    def check_advance_criteria(self, target_id: int) -> dict:
        """Check if target meets criteria to advance maturity."""
        with self.get_db() as db:
            t = db.query(TargetModel).options(
                joinedload(TargetModel.benchmarks),
            ).filter(TargetModel.id == target_id).first()
            if not t:
                return {"can_advance": False, "reason": "Target not found"}
            if t.maturity_level >= 5:
                return {"can_advance": False, "reason": "Already at L5 (Solved)"}
            if t.status != "active":
                return {"can_advance": False, "reason": f"Target is {t.status}, must be active"}

            lvl = t.maturity_level
            reasons = []

            if lvl == 0:
                if not t.benchmarks:
                    reasons.append("At least 1 benchmark must be defined")
            elif lvl == 1:
                if t.target_score and t.current_score is not None:
                    if t.current_score < t.target_score * 0.5:
                        reasons.append(f"Score {t.current_score} < 50% of target {t.target_score}")
                else:
                    reasons.append("target_score and current_score must be set")
            elif lvl == 2:
                if t.target_score and t.current_score is not None:
                    if t.current_score < t.target_score * 0.8:
                        reasons.append(f"Score {t.current_score} < 80% of target {t.target_score}")
                benchmarks_without_values = [b for b in t.benchmarks if b.current_value is None]
                if benchmarks_without_values:
                    reasons.append(f"{len(benchmarks_without_values)} benchmarks missing values")
            elif lvl == 3:
                if t.target_score and t.current_score is not None:
                    if t.current_score < t.target_score * 0.9:
                        reasons.append(f"Score {t.current_score} < 90% of target {t.target_score}")
                if not t.success_criteria:
                    reasons.append("success_criteria must be defined")
            elif lvl == 4:
                if t.target_score and t.current_score is not None:
                    if t.current_score < t.target_score * 0.95:
                        reasons.append(f"Score {t.current_score} < 95% of target {t.target_score}")

            if reasons:
                return {"can_advance": False, "reason": "; ".join(reasons), "unmet": reasons}
            return {"can_advance": True, "from_level": lvl, "to_level": lvl + 1}

    def advance_target(self, target_id: int) -> Optional[dict]:
        with self.get_db() as db:
            t = db.query(TargetModel).filter(TargetModel.id == target_id).first()
            if not t or t.maturity_level >= 5:
                return None
            old_level = t.maturity_level
            t.maturity_level = old_level + 1
            if t.maturity_level == 5:
                t.status = "completed"
            db.commit()
            db.refresh(t)
            return {"from_level": old_level, "to_level": t.maturity_level}

    # ── Benchmarks ───────────────────────────────────────────────────
    def add_benchmark(self, target_id: int, data: dict) -> dict:
        with self.get_db() as db:
            b = BenchmarkModel(target_id=target_id, **data)
            db.add(b)
            db.commit()
            db.refresh(b)
            return self._benchmark_to_dict(b)

    def update_benchmark(self, benchmark_id: int, data: dict) -> Optional[dict]:
        with self.get_db() as db:
            b = db.query(BenchmarkModel).filter(BenchmarkModel.id == benchmark_id).first()
            if not b:
                return None
            for k, v in data.items():
                if v is not None and hasattr(b, k):
                    setattr(b, k, v)

            if "current_value" in data and data["current_value"] is not None:
                history = BenchmarkHistoryModel(
                    target_id=b.target_id,
                    benchmark_id=b.id,
                    value=data["current_value"],
                )
                db.add(history)

            db.commit()
            db.refresh(b)
            return self._benchmark_to_dict(b)

    def get_benchmark_history(self, target_id: int, benchmark_id: Optional[int] = None, limit: int = 100) -> list:
        with self.get_db() as db:
            q = db.query(BenchmarkHistoryModel).filter(BenchmarkHistoryModel.target_id == target_id)
            if benchmark_id:
                q = q.filter(BenchmarkHistoryModel.benchmark_id == benchmark_id)
            entries = q.order_by(BenchmarkHistoryModel.recorded_at.desc()).limit(limit).all()
            return [
                {"id": e.id, "benchmark_id": e.benchmark_id, "value": e.value, "recorded_at": str(e.recorded_at)}
                for e in entries
            ]

    # ── Resources ────────────────────────────────────────────────────
    def add_resource(self, target_id: int, data: dict) -> dict:
        with self.get_db() as db:
            r = ResourceModel(target_id=target_id, **data)
            db.add(r)
            db.commit()
            db.refresh(r)
            return self._resource_to_dict(r)

    def update_resource(self, resource_id: int, data: dict) -> Optional[dict]:
        with self.get_db() as db:
            r = db.query(ResourceModel).filter(ResourceModel.id == resource_id).first()
            if not r:
                return None
            for k, v in data.items():
                if v is not None and hasattr(r, k):
                    setattr(r, k, v)

            alerts = []
            if r.alert_at and r.consumed >= r.alert_at:
                alerts.append({"type": "budget_alert", "resource": r.resource_type, "consumed": r.consumed, "alert_at": r.alert_at})
            if r.hard_limit and r.consumed >= r.hard_limit:
                alerts.append({"type": "budget_exceeded", "resource": r.resource_type, "consumed": r.consumed, "hard_limit": r.hard_limit})

            db.commit()
            db.refresh(r)
            result = self._resource_to_dict(r)
            result["alerts"] = alerts
            return result

    # ── Audit ────────────────────────────────────────────────────────
    def log_event(self, user_id: int, target_id: Optional[int], event_type: str, details: dict = None):
        with self.get_db() as db:
            last = db.query(AuditEventModel).order_by(AuditEventModel.id.desc()).first()
            prev_hash = last.event_hash if last else "genesis"

            event_data = json.dumps({
                "user_id": user_id,
                "target_id": target_id,
                "event_type": event_type,
                "details": details or {},
                "prev_hash": prev_hash,
            }, sort_keys=True)
            event_hash = hashlib.sha256(event_data.encode()).hexdigest()[:32]

            evt = AuditEventModel(
                user_id=user_id,
                target_id=target_id,
                event_type=event_type,
                details=details or {},
                prev_hash=prev_hash,
                event_hash=event_hash,
            )
            db.add(evt)
            db.commit()

    def get_audit_events(self, target_id: Optional[int] = None, user_id: Optional[int] = None,
                         event_type: Optional[str] = None, limit: int = 100, offset: int = 0) -> tuple:
        with self.get_db() as db:
            q = db.query(AuditEventModel)
            if target_id:
                q = q.filter(AuditEventModel.target_id == target_id)
            if user_id:
                q = q.filter(AuditEventModel.user_id == user_id)
            if event_type:
                q = q.filter(AuditEventModel.event_type == event_type)
            total = q.count()
            events = q.order_by(AuditEventModel.created_at.desc()).offset(offset).limit(limit).all()
            return [
                {
                    "id": e.id,
                    "user_id": e.user_id,
                    "target_id": e.target_id,
                    "event_type": e.event_type,
                    "details": e.details,
                    "event_hash": e.event_hash,
                    "created_at": str(e.created_at) if e.created_at else None,
                }
                for e in events
            ], total

    # ── Pipeline Analytics ───────────────────────────────────────────
    def get_pipeline_summary(self, user_id: int) -> dict:
        with self.get_db() as db:
            active = db.query(TargetModel).filter(
                TargetModel.user_id == user_id, TargetModel.status == "active"
            ).all()

            summary = {str(i): 0 for i in range(6)}
            total_maturity = 0
            for t in active:
                lvl = t.maturity_level
                if 0 <= lvl <= 5:
                    summary[str(lvl)] += 1
                total_maturity += lvl

            avg_maturity = round(total_maturity / len(active), 2) if active else 0

            bottlenecks = []
            for t in sorted(active, key=lambda x: x.updated_at or x.created_at):
                age_days = (datetime.now(timezone.utc) - (t.updated_at or t.created_at).replace(tzinfo=timezone.utc)).days
                if age_days > 7:
                    bottlenecks.append({
                        "target_id": t.id,
                        "title": t.title,
                        "maturity_level": t.maturity_level,
                        "days_stuck": age_days,
                    })

            return {
                "summary": summary,
                "total_active": len(active),
                "avg_maturity": avg_maturity,
                "bottlenecks": sorted(bottlenecks, key=lambda x: -x["days_stuck"])[:10],
            }

    # ── Helpers ──────────────────────────────────────────────────────
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
            "benchmarks": [self._benchmark_to_dict(b) for b in (t.benchmarks or [])],
            "resources": [self._resource_to_dict(r) for r in (t.resources or [])],
            "created_at": str(t.created_at) if t.created_at else None,
            "updated_at": str(t.updated_at) if t.updated_at else None,
        }

    def _benchmark_to_dict(self, b: BenchmarkModel) -> dict:
        return {
            "id": b.id,
            "name": b.name,
            "metric_type": b.metric_type,
            "current_value": b.current_value,
            "target_value": b.target_value,
            "unit": b.unit,
            "recorded_at": str(b.recorded_at) if b.recorded_at else None,
        }

    def _resource_to_dict(self, r: ResourceModel) -> dict:
        return {
            "id": r.id,
            "resource_type": r.resource_type,
            "allocated": r.allocated,
            "consumed": r.consumed,
            "unit": r.unit,
            "alert_at": r.alert_at,
            "hard_limit": r.hard_limit,
        }


repo = Repository()
