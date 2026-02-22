"""FastAPI application entry point — mirrors CompareGPT pattern."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.core.config import settings
from backend.db.models import Base, engine, SessionLocal, TargetModel, BenchmarkModel, ResourceModel, UserModel
from backend.routers.user import router as user_router
from backend.routers.target import router as target_router
from backend.routers.system import router as system_router
from backend.services.auth_service import DEMO_USER_ID

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)


def seed_demo_data():
    """Seed demo targets for unauthenticated visitors."""
    db = SessionLocal()
    try:
        existing = db.query(TargetModel).filter(TargetModel.user_id == DEMO_USER_ID).count()
        if existing > 0:
            return

        # Ensure demo user exists
        demo_user = db.query(UserModel).filter(UserModel.user_id == DEMO_USER_ID).first()
        if not demo_user:
            db.add(UserModel(user_id=DEMO_USER_ID, user_name="Demo", role="demo"))

        demo_targets = [
            {
                "title": "Medical Diagnosis Accuracy",
                "description": "Improve AI-assisted diagnostic accuracy for radiology imaging across 12 pathology types.",
                "domain": "Healthcare",
                "maturity_level": 2,
                "priority": "critical",
                "current_score": 72.5,
                "target_score": 95.0,
                "tags": ["radiology", "diagnostics", "deep-learning"],
                "success_criteria": "95% concordance with specialist panel across all 12 pathology types",
                "benchmarks": [
                    {"name": "Sensitivity", "metric_type": "percentage", "current_value": 78.3, "target_value": 95.0, "unit": "%"},
                    {"name": "Specificity", "metric_type": "percentage", "current_value": 91.2, "target_value": 98.0, "unit": "%"},
                ],
                "resources": [
                    {"resource_type": "compute", "allocated": 500, "unit": "GPU-hours", "alert_at": 400, "hard_limit": 500},
                ],
            },
            {
                "title": "Autonomous Code Review",
                "description": "Build an AI system that reviews pull requests with human-level accuracy, detecting bugs, security issues, and style violations.",
                "domain": "Infrastructure",
                "maturity_level": 1,
                "priority": "high",
                "current_score": 35.0,
                "target_score": 90.0,
                "tags": ["code-review", "security", "automation"],
                "benchmarks": [
                    {"name": "Bug Detection Rate", "metric_type": "percentage", "current_value": 42.0, "target_value": 90.0, "unit": "%"},
                    {"name": "False Positive Rate", "metric_type": "percentage", "current_value": 28.0, "target_value": 5.0, "unit": "%"},
                ],
                "resources": [
                    {"resource_type": "api_calls", "allocated": 10000, "unit": "requests", "alert_at": 8000},
                ],
            },
            {
                "title": "Climate Risk Assessment",
                "description": "Predict infrastructure vulnerability to climate events using satellite imagery and historical weather data.",
                "domain": "Climate",
                "maturity_level": 0,
                "priority": "high",
                "tags": ["satellite", "climate", "risk-modeling"],
                "target_score": 85.0,
                "benchmarks": [
                    {"name": "Prediction Accuracy", "metric_type": "score", "target_value": 85.0, "unit": "%"},
                ],
            },
            {
                "title": "Research Paper Synthesis",
                "description": "Automatically synthesize findings across thousands of research papers to identify consensus, contradictions, and gaps.",
                "domain": "Research",
                "maturity_level": 3,
                "priority": "medium",
                "current_score": 81.0,
                "target_score": 92.0,
                "tags": ["NLP", "meta-analysis", "knowledge-graph"],
                "success_criteria": "Expert panel rates synthesis quality >= 4.5/5 across 100 random topics",
                "benchmarks": [
                    {"name": "Synthesis Quality", "metric_type": "score", "current_value": 4.1, "target_value": 4.5, "unit": "/5"},
                    {"name": "Coverage", "metric_type": "percentage", "current_value": 87.0, "target_value": 95.0, "unit": "%"},
                ],
                "resources": [
                    {"resource_type": "tokens", "allocated": 50000000, "unit": "tokens", "alert_at": 40000000},
                ],
            },
            {
                "title": "Fraud Detection Pipeline",
                "description": "Real-time transaction fraud detection with sub-100ms latency and < 0.1% false positive rate.",
                "domain": "Finance",
                "maturity_level": 4,
                "priority": "critical",
                "current_score": 94.2,
                "target_score": 99.0,
                "tags": ["fraud", "real-time", "ML-pipeline"],
                "success_criteria": "99% detection rate, <0.1% FPR, <100ms p95 latency for 30 consecutive days",
                "benchmarks": [
                    {"name": "Detection Rate", "metric_type": "percentage", "current_value": 96.8, "target_value": 99.0, "unit": "%"},
                    {"name": "P95 Latency", "metric_type": "score", "current_value": 67.0, "target_value": 100.0, "unit": "ms"},
                ],
                "resources": [
                    {"resource_type": "compute", "allocated": 2000, "unit": "vCPU-hours", "alert_at": 1600, "hard_limit": 2000},
                ],
            },
            {
                "title": "Adaptive Learning Platform",
                "description": "Personalized education system that adjusts difficulty and content in real-time based on student performance.",
                "domain": "Education",
                "maturity_level": 1,
                "priority": "medium",
                "current_score": 28.0,
                "target_score": 80.0,
                "tags": ["edtech", "personalization", "reinforcement-learning"],
                "benchmarks": [
                    {"name": "Learning Gain", "metric_type": "percentage", "current_value": 15.0, "target_value": 40.0, "unit": "%"},
                ],
            },
        ]

        for tdata in demo_targets:
            benchmarks = tdata.pop("benchmarks", [])
            resources = tdata.pop("resources", [])
            t = TargetModel(user_id=DEMO_USER_ID, **tdata)
            db.add(t)
            db.flush()
            for b in benchmarks:
                db.add(BenchmarkModel(target_id=t.id, **b))
            for r in resources:
                db.add(ResourceModel(target_id=t.id, **r))

        db.commit()
        logger.info("Seeded %d demo targets.", len(demo_targets))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
    seed_demo_data()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(user_router)
app.include_router(target_router)
app.include_router(system_router)

# Serve built frontend (after API routes so /api/* takes priority)
dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
