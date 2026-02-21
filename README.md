# Intelligence Orchestrator — Targeting System

A personal intelligence orchestrator targeting system built on the [SolveEverything](https://solveeverything.org/) methodology. Define, track, and advance intelligence targets through the L0–L5 maturity pipeline.

**Live:** https://orche.platformai.org

## What is this?

The Targeting System is the **rail** (infrastructure) of the Intelligence Orchestrator — it provides the framework for defining *what* to solve, *how* to measure progress, and *when* a problem is solved. Based on the SolveEverything maturity model:

| Level | Label | Description |
|-------|-------|-------------|
| L0 | Unmeasured | Problem exists but no metrics defined |
| L1 | Measured | Metrics defined, manual process |
| L2 | Assisted | AI-assisted with human oversight |
| L3 | Automated | Automated with audit trail |
| L4 | Industrialized | Scaled, reliable, cost-effective |
| L5 | Solved | Commoditized — problem solved |

## Features

- **Dashboard** — KPI overview, maturity distribution chart, pipeline view
- **Maturity Pipeline** — Visual L0–L5 progression board
- **Target Management** — Create, edit, delete intelligence targets with benchmarks and resource tracking
- **Benchmark Tracking** — Define measurable benchmarks (accuracy, latency, cost) with current vs target values
- **Resource Governance** — Track compute, budget, tokens, and time allocation per target
- **SSO Authentication** — Optional CompareGPT SSO integration

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLite + SQLAlchemy |
| Frontend | Vue 3 + TypeScript + Vite |
| Auth | JWT + CompareGPT SSO |
| Deployment | PM2 + Nginx + Let's Encrypt |

## Project Structure

```
targeting_sys/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── core/config.py           # Pydantic settings
│   ├── db/
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   └── repo.py              # Data access layer
│   ├── routers/
│   │   ├── target.py            # Target CRUD endpoints
│   │   ├── user.py              # Auth endpoints
│   │   └── system.py            # Health & status
│   └── services/
│       └── auth_service.py      # SSO + JWT auth
├── frontend/
│   ├── src/
│   │   ├── views/               # DashboardView, TargetDetailView
│   │   ├── components/          # AppHeader, MaturityPipeline, TargetCard, MetricsPanel, CreateTargetModal
│   │   ├── stores/              # Pinia stores (auth, targeting)
│   │   ├── services/api.ts      # HTTP client
│   │   ├── types/index.ts       # TypeScript interfaces
│   │   └── assets/main.css      # Design system
│   └── dist/                    # Built output
├── ecosystem.config.js          # PM2 config
├── nginx.conf                   # Nginx reference config
├── requirements.txt             # Python dependencies
└── start.sh                     # Startup script
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/targets` | Create a new intelligence target |
| `GET` | `/api/targets` | List targets (filterable by status) |
| `GET` | `/api/targets/maturity-summary` | L0–L5 distribution counts |
| `GET` | `/api/targets/{id}` | Get target detail |
| `PUT` | `/api/targets/{id}` | Update target |
| `DELETE` | `/api/targets/{id}` | Delete target |
| `POST` | `/api/user/validate` | SSO token exchange / JWT validation |
| `GET` | `/api/system/health` | Health check |
| `GET` | `/api/system/status` | System status |

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+ or 22+
- PM2 (`npm install -g pm2`)

### Install & Run

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies & build
cd frontend
npm install
npx vite build
cd ..

# Start services
pm2 start ecosystem.config.js
```

Backend runs on `http://127.0.0.1:8000`, frontend preview on `http://127.0.0.1:4173`.

### Environment Variables

Copy `.env.example` or create `.env`:

```env
ENV=production
APP_PORT=8000
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./backend/data/targeting.db
SSO_VALIDATE_URL=https://comparegpt.io/api/sso/validate
DOMAIN=orche.platformai.org
SERVER_IP=34.63.169.185
```

### Nginx + SSL

```bash
# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/orche.platformai.org
sudo ln -s /etc/nginx/sites-available/orche.platformai.org /etc/nginx/sites-enabled/

# Get SSL certificate
sudo certbot --nginx -d orche.platformai.org

# Reload
sudo systemctl reload nginx
```

## Architecture

Based on [CompareGPT-AIScientist](https://github.com/CompareGPT-io/CompareGPT-AIScientist) patterns:

- **Backend:** FastAPI with Pydantic settings, SQLAlchemy ORM, repository pattern
- **Frontend:** Vue 3 Composition API, Pinia state management, dark-first design system
- **Auth:** SSO token exchange → JWT, with public fallback for demo access
- **Deploy:** PM2 process management, Nginx reverse proxy, Let's Encrypt SSL

## License

MIT
