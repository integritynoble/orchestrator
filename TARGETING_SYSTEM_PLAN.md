# Targeting System Plan

## Intelligence Orchestrator — Targeting System Development Plan

Based on: `Intelligence Orchestrator.docx` PRD + SolveEverything methodology

---

## 1. Vision

The Targeting System is the **strategic brain** of the Intelligence Orchestrator. It answers three fundamental questions:

1. **WHAT** to solve — define intelligence targets with measurable benchmarks
2. **HOW WELL** it's going — track progress through the L0–L5 maturity pipeline
3. **WHAT IT COSTS** — govern resources (compute, budget, tokens, time) per target

It is the **rail**, not the train. The rail decides where intelligence gets routed; the trains (Claude Code, Codex CLI, OpenClaw, custom skills) ride on top.

---

## 2. Principles Applied to Targeting

From the PRD, the targeting system enforces:

| PRD Principle | Targeting System Implementation |
|---|---|
| User sovereignty | User defines targets, owns all data, can export |
| Least privilege | Targets declare required capabilities before execution |
| Auditable & reversible | Every target change logged in immutable audit trail |
| Policy-first | Targets checked against policy before task dispatch |
| Deterministic core + LLM edges | Core CRUD/pipeline logic is deterministic; LLM assists planning & decomposition |
| Capability-based skills | Each target maps to skills with declared contracts |
| Resource governance | Per-target budgets with hard limits and alerts |
| Safe failure | Targets fail closed; auto-pause on budget exhaustion |

---

## 3. Architecture

### 3.1 System Context

```
┌─────────────────────────────────────────────────┐
│                  User (Browser)                  │
│   Dashboard / Pipeline / Target Detail / Create  │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────┐
│              Nginx (orche.platformai.org)         │
│         SSL termination + reverse proxy          │
└──────┬──────────────────────────────┬────────────┘
       │ /api/*                       │ /*
       ▼                              ▼
┌──────────────┐            ┌─────────────────┐
│   FastAPI     │            │   Vue 3 SPA     │
│   Backend     │            │   (Static)      │
│   :8000       │            │   /dist/        │
└──────┬───────┘            └─────────────────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SQLite/    │    │  Policy      │    │  Audit       │
│   PostgreSQL │    │  Engine      │    │  Logger      │
│   (targets,  │    │  (cap check) │    │  (immutable) │
│   benchmarks)│    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 3.2 Orchestration Loop Integration

The targeting system feeds into the PRD's 7-step orchestration loop:

```
1. PERCEIVE  ← Targeting System provides: active targets, current scores, resource state
2. PLAN      ← Targeting System provides: priority ranking, maturity gap analysis
3. PERMIT    ← Targeting System provides: required capabilities per target
4. ACT       ← Task engine executes steps against target benchmarks
5. VERIFY    ← Benchmark scores updated, pass/fail against success criteria
6. LOG       ← Audit events recorded per target
7. REFLECT   ← Maturity level advanced if criteria met
```

---

## 4. Data Model

### 4.1 Core Entities

```
┌────────────────┐       ┌────────────────┐       ┌────────────────┐
│     Target     │──1:N──│   Benchmark    │       │    Resource     │
│                │       │                │       │   Allocation    │
│ id             │       │ id             │       │ id              │
│ user_id        │       │ target_id (FK) │       │ target_id (FK)  │
│ title          │       │ name           │       │ resource_type   │
│ description    │       │ metric_type    │       │ allocated       │
│ domain         │       │ current_value  │       │ consumed        │
│ maturity_level │       │ target_value   │       │ unit            │
│ status         │       │ unit           │       │ budget_alert_at │
│ priority       │       │ recorded_at    │       │ hard_limit      │
│ benchmark_def  │       └────────────────┘       └────────────────┘
│ success_crit   │
│ current_score  │       ┌────────────────┐       ┌────────────────┐
│ target_score   │──1:N──│  Target Task   │──1:N──│  Audit Event   │
│ tags           │       │                │       │                │
│ config         │       │ id             │       │ id             │
│ created_at     │       │ target_id (FK) │       │ target_id      │
│ updated_at     │       │ task_id (FK)   │       │ event_type     │
└────────────────┘       │ status         │       │ actor          │
                         │ tool_used      │       │ details (JSON) │
       1:N               │ result         │       │ hash (chain)   │
        │                └────────────────┘       │ created_at     │
        ▼                                         └────────────────┘
┌────────────────┐
│ Capability Req │
│                │
│ id             │
│ target_id (FK) │
│ capability     │   fs.read | fs.write | proc.exec | net.egress | secrets.read
│ scope          │   path:/... | cmd:... | domain:...
│ approved       │
│ approved_until │
└────────────────┘
```

### 4.2 Maturity Level Schema (SolveEverything L0–L5)

| Level | Label | Entry Criteria | Exit Criteria |
|-------|-------|---------------|---------------|
| L0 | Unmeasured | Problem identified | Benchmarks defined, baseline measured |
| L1 | Measured | Baseline metrics exist | AI-assisted prototype achieves >50% of target |
| L2 | Assisted | AI prototype running | Automated pipeline with human review achieves >80% |
| L3 | Automated | Pipeline automated | Passes blinded adversarial test suite, audit trail complete |
| L4 | Industrialized | Adversarial-tested | Cost < threshold, SLA met for 30 days, handles edge cases |
| L5 | Solved | Industrialized + stable | Commoditized: public API, <1% failure, self-healing |

### 4.3 Priority Classification

| Priority | SLA | Auto-escalation | Resource Cap |
|----------|-----|-----------------|-------------|
| Critical | Tasks dispatched within 1 min | Alert after 15 min stall | No cap (user-approved) |
| High | Tasks dispatched within 5 min | Alert after 1 hr stall | 2x base budget |
| Medium | Tasks dispatched within 30 min | Alert after 4 hr stall | 1x base budget |
| Low | Best-effort queue | No auto-escalation | 0.5x base budget |

---

## 5. API Design

### 5.1 Target APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/targets` | Create target |
| `GET` | `/api/targets` | List targets (filter: status, priority, domain, maturity_level) |
| `GET` | `/api/targets/{id}` | Get target detail with benchmarks, resources, tasks |
| `PUT` | `/api/targets/{id}` | Update target |
| `DELETE` | `/api/targets/{id}` | Delete target (soft delete → archived) |
| `POST` | `/api/targets/{id}/advance` | Advance maturity level (validates exit criteria) |
| `POST` | `/api/targets/{id}/pause` | Pause target (suspends associated tasks) |
| `POST` | `/api/targets/{id}/dispatch` | Dispatch target to orchestration loop |

### 5.2 Benchmark APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/targets/{id}/benchmarks` | Add benchmark |
| `PUT` | `/api/targets/{id}/benchmarks/{bid}` | Update benchmark value |
| `GET` | `/api/targets/{id}/benchmarks/history` | Benchmark value history (time series) |
| `POST` | `/api/targets/{id}/benchmarks/evaluate` | Run blinded evaluation |

### 5.3 Resource APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/targets/{id}/resources` | Allocate resource |
| `PUT` | `/api/targets/{id}/resources/{rid}` | Update allocation/consumed |
| `GET` | `/api/targets/{id}/resources/usage` | Resource consumption report |
| `POST` | `/api/targets/{id}/resources/alert` | Set budget alert threshold |

### 5.4 Pipeline APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/pipeline/summary` | Maturity distribution + KPIs |
| `GET` | `/api/pipeline/bottlenecks` | Targets stuck at a level longest |
| `GET` | `/api/pipeline/velocity` | Avg time per maturity transition |
| `GET` | `/api/pipeline/forecast` | Projected completion dates |

### 5.5 Audit APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/targets/{id}/audit` | Audit trail for target |
| `GET` | `/api/audit/export` | Export audit log (CSV/JSON) |

---

## 6. Frontend Pages

### 6.1 Dashboard (current: implemented)

```
┌──────────────────────────────────────────────────────────────┐
│  [Logo] Intelligence Orchestrator  TARGETING    [Sign In]    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                       │
│  │  5   │ │ 2.2  │ │  0   │ │  2   │  KPI Cards            │
│  │Active│ │ Avg  │ │Compl.│ │Crit. │                       │
│  └──────┘ └──────┘ └──────┘ └──────┘                       │
│                                                              │
│  Maturity Distribution  [bar chart L0-L5]                    │
│                                                              │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┐  Maturity Pipeline  │
│  │ L0  │ L1  │ L2  │ L3  │ L4  │ L5  │                     │
│  │     │     │     │     │     │     │                      │
│  │cards│cards│cards│cards│cards│cards│                      │
│  └─────┴─────┴─────┴─────┴─────┴─────┘                     │
│                                                              │
│  Intelligence Targets        [filter ▼]  [+ New Target]     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ Target 1 │ │ Target 2 │ │ Target 3 │  Target Cards       │
│  │ progress │ │ progress │ │ progress │                     │
│  └──────────┘ └──────────┘ └──────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Target Detail (current: implemented)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                        │
│                                                              │
│  Target Title                    [Advance L→] [Edit] [Del]  │
│  [L2 Assisted] [active] [high] [Healthcare]                 │
│  Description text...                                         │
│  ━━━━━━━━━━━━━━━━━━━━ 72/95 (75%) ━━━━━━━━━━                │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ Benchmark Def.  │  │ Success Criteria│                   │
│  │ ...             │  │ ...             │                   │
│  ├─────────────────┤  ├─────────────────┤                   │
│  │ Benchmarks (3)  │  │ Resources (2)   │                   │
│  │ name  cur / tgt │  │ type  used/alloc│                   │
│  │ ...             │  │ ...             │                   │
│  └─────────────────┘  └─────────────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

### 6.3 Pipeline View (planned: Phase 2)

Full-screen Kanban-style board with drag-and-drop between maturity levels. Includes:
- Velocity sparklines per level
- Bottleneck indicators (time stuck)
- Filter by domain, priority, status

### 6.4 Analytics View (planned: Phase 3)

- Return on Cognitive Spend (RoCS) charts
- Benchmark trend lines over time
- Resource burn-down charts
- Maturity velocity by domain
- Forecasted completion dates

### 6.5 Dispatch View (planned: Phase 4)

- Target → Task mapping
- Orchestration loop status per target
- Capability approval queue
- Live task execution feed

---

## 7. Development Phases

### Phase 1 — Foundation (current: DONE)

**Goal:** Working webpage with target CRUD and maturity pipeline visualization.

| Deliverable | Status |
|---|---|
| FastAPI backend with Target/Benchmark/Resource CRUD | Done |
| Vue 3 dashboard with KPIs, pipeline, target cards | Done |
| Create/edit/delete targets with benchmarks & resources | Done |
| SQLite database with full schema | Done |
| PM2 + Nginx + SSL deployment on orche.platformai.org | Done |
| GitHub repo at integritynoble/orchestrator | Done |
| Demo data seeded (6 targets across L0–L4) | Done |

### Phase 2 — Pipeline Intelligence

**Goal:** Make the pipeline smart — auto-evaluate maturity transitions, benchmark history, bottleneck detection.

| Deliverable | Description |
|---|---|
| Maturity transition rules engine | Validate exit criteria before advancing L0→L1→...→L5 |
| Benchmark history tracking | Time-series storage, trend charts in UI |
| Pipeline analytics API | `/api/pipeline/summary`, `/api/pipeline/bottlenecks`, `/api/pipeline/velocity` |
| Full-screen pipeline Kanban view | Drag-and-drop targets between levels (with validation) |
| Bottleneck alerts | Highlight targets stuck at a level beyond threshold |
| Benchmark evaluation runner | Trigger blinded test evaluations, record results |

### Phase 3 — Resource Governance & Analytics

**Goal:** Implement the PRD's resource governance — budgets, alerts, cost tracking, RoCS.

| Deliverable | Description |
|---|---|
| Per-target budget enforcement | Hard limits with auto-pause on exhaustion |
| Budget alert system | Configurable thresholds (50%, 80%, 95%) with notifications |
| Resource consumption dashboard | Burn-down charts, allocation vs actual |
| Return on Cognitive Spend (RoCS) | Track (maturity gain / resources consumed) per target |
| Cost forecasting | Project resource needs based on velocity |
| Export & reporting | CSV/JSON export of resource usage per target |

### Phase 4 — Orchestration Loop Integration

**Goal:** Connect targeting to the PRD's orchestration loop (Perceive→Plan→Permit→Act→Verify→Log→Reflect).

| Deliverable | Description |
|---|---|
| Target dispatch API | `/api/targets/{id}/dispatch` → creates task in orchestration loop |
| Capability requirements | Targets declare required capabilities (fs.read, proc.exec, etc.) |
| Approval gate UI | Permission prompts per PRD spec (allow once / allow for task / deny) |
| Task-target binding | Tasks linked to targets, results feed back to benchmarks |
| Tool router integration | Route target tasks to appropriate tool (Claude Code, Codex, OpenClaw) |
| Audit trail per target | Immutable log with chain-hashing |

### Phase 5 — Policy Engine & Permissions

**Goal:** Implement PRD's policy-first orchestration for targeting.

| Deliverable | Description |
|---|---|
| Policy engine | Check capabilities before dispatch, enforce safe mode |
| Capability grant management | Grant/revoke/expire scoped permissions |
| Safe mode defaults | New targets default to safe mode (no network, no sudo, limited CPU) |
| Risk scoring | Auto-classify target risk based on required capabilities |
| Escalation rules | Auto-escalate to user on high-risk capability requests |

### Phase 6 — Skill Marketplace Integration

**Goal:** Connect targets to installable skills from the PRD's skill registry.

| Deliverable | Description |
|---|---|
| Skill-target mapping | Recommend skills for each target based on domain/capabilities |
| Skill install from target | One-click install required skills for a target |
| Skill manifest validation | Validate capabilities match target requirements |
| Skill execution tracking | Track which skills contributed to benchmark improvements |

### Phase 7 — Hardening & Scale

**Goal:** Production-grade reliability per PRD Phase 7.

| Deliverable | Description |
|---|---|
| PostgreSQL migration | Move from SQLite to PostgreSQL for concurrent access |
| Row-level security | Tenant isolation via user_id scoping |
| Snapshot & restore | Pre-task snapshots, rollback on failure |
| Abuse detection | Rate limiting, anomaly detection on target creation |
| SLO monitoring | Dashboard for API latency, error rates, uptime |
| Backup automation | Scheduled database backups with retention policy |

---

## 8. Orchestration Loop Detail

For each active target, the orchestrator runs this loop:

```
┌─────────────────────────────────────────────────────────┐
│                    TARGETING LOOP                        │
│                                                         │
│  ┌─────────┐    Target provides context:                │
│  │PERCEIVE │ ←  current_score, maturity_level,          │
│  │         │    benchmark values, resource state         │
│  └────┬────┘                                            │
│       ▼                                                  │
│  ┌─────────┐    Target provides:                         │
│  │  PLAN   │ ←  success_criteria → step DAG             │
│  │         │    benchmark_definition → test plan          │
│  └────┬────┘    priority → scheduling weight             │
│       ▼                                                  │
│  ┌─────────┐    Target declares:                         │
│  │ PERMIT  │ ←  required capabilities                   │
│  │         │    User approves via permission prompt UI   │
│  └────┬────┘                                            │
│       ▼                                                  │
│  ┌─────────┐    Dispatched to:                           │
│  │  ACT    │ ←  workspace (safe) or ephemeral sandbox   │
│  │         │    via tool router (Claude/Codex/OpenClaw)  │
│  └────┬────┘                                            │
│       ▼                                                  │
│  ┌─────────┐    Updated:                                 │
│  │ VERIFY  │ ←  benchmark scores re-evaluated           │
│  │         │    success criteria checked                  │
│  └────┬────┘    pass → advance maturity                  │
│       ▼                                                  │
│  ┌─────────┐    Recorded:                                │
│  │  LOG    │ ←  audit event (immutable, chain-hashed)   │
│  │         │    resource consumption updated              │
│  └────┬────┘                                            │
│       ▼                                                  │
│  ┌─────────┐    Updated:                                 │
│  │REFLECT  │ ←  maturity_level if criteria met          │
│  │         │    memory: what worked, what didn't         │
│  └─────────┘                                            │
└─────────────────────────────────────────────────────────┘
```

---

## 9. Permission Prompt Integration

When a target is dispatched, the system generates permission prompts per the PRD:

### Example: Target "Automated Clinical Trial Analysis" dispatched

```
┌──────────────────────────────────────────────────┐
│  Allow file access?                              │
│                                                  │
│  The orchestrator needs to read files in:        │
│  /home/user/clinical-data/                       │
│                                                  │
│  Purpose: Analyze trial data for Target #1       │
│  Capability: fs.read                             │
│  Scope: path:/home/user/clinical-data/           │
│                                                  │
│  [Allow once]  [Allow for this task]  [Deny]     │
│                                                  │
│  ▸ Advanced: Change scope | Require review       │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  Allow command execution?                        │
│                                                  │
│  Command: python3 analyze_trials.py              │
│  Working dir: /home/user/clinical-data/          │
│  Safe Mode: ON                                   │
│                                                  │
│  [Allow for this task]  [Deny]  [Edit command]   │
└──────────────────────────────────────────────────┘
```

---

## 10. Resource Governance Model

Per the PRD's Principle 8 (Resource governance and cost predictability):

```
Per-Target Budget Structure:
├── Compute
│   ├── allocated: 1000 GPU-hrs
│   ├── consumed: 420 GPU-hrs
│   ├── alert_at: 800 GPU-hrs (80%)
│   └── hard_limit: 1000 GPU-hrs (auto-pause)
├── Budget (USD)
│   ├── allocated: $50,000
│   ├── consumed: $18,000
│   ├── alert_at: $40,000
│   └── hard_limit: $50,000
├── Tokens (LLM)
│   ├── allocated: 10M tokens
│   ├── consumed: 6.5M tokens
│   └── alert_at: 8M tokens
└── Time
    ├── allocated: 90 days
    ├── elapsed: 34 days
    └── alert_at: 75 days
```

### RoCS (Return on Cognitive Spend)

```
RoCS = Maturity Gain / Normalized Resource Cost

Example:
  Target: Clinical Trial Analysis
  Maturity: L0 → L1 (gain = 1)
  Cost: 420 GPU-hrs ($18,000)
  RoCS = 1 / 18000 = 0.000056 maturity-points per dollar

Compare across targets to identify:
  - High-ROI targets (invest more)
  - Low-ROI targets (re-evaluate approach or pause)
```

---

## 11. Technology Roadmap

| Phase | Timeline | Key Technology |
|-------|----------|---------------|
| Phase 1 (Done) | Week 1 | FastAPI + Vue 3 + SQLite + Nginx |
| Phase 2 | Week 2–3 | Benchmark history (time-series), Kanban UI |
| Phase 3 | Week 4–5 | Resource governance, budget alerts, analytics charts |
| Phase 4 | Week 6–8 | Orchestration loop, task dispatch, tool router |
| Phase 5 | Week 9–10 | Policy engine, capability grants, safe mode |
| Phase 6 | Week 11–13 | Skill marketplace, manifest validation |
| Phase 7 | Week 14–16 | PostgreSQL, RLS, snapshots, SLO monitoring |

---

## 12. Success Criteria (v1 Ship Bar)

From the PRD:

- [ ] User can create, view, edit, delete intelligence targets
- [ ] Targets track maturity through L0–L5 with defined transition criteria
- [ ] Benchmarks are measurable and tracked over time
- [ ] Resources are allocated per target with budget enforcement
- [ ] Pipeline view shows maturity distribution and bottlenecks
- [ ] Audit trail records every target change
- [ ] Permission prompts appear before capability escalation
- [ ] Orchestration loop dispatches tasks against targets
- [ ] Results feed back to benchmark scores automatically
- [ ] RoCS metric enables cross-target resource optimization
