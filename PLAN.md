# PLAN.md — Targeting System Implementation Plan

## Overview

Implement the full Targeting System for the Intelligence Orchestrator, with authentication matching the CompareGPT-AIScientist SSO flow exactly.

**Live URL:** https://orche.platformai.org
**Repo:** https://github.com/integritynoble/orchestrator
**Server:** 34.63.169.185
**Domain:** orche.platformai.org

---

## Phase 1: Authentication (CompareGPT SSO Method) — PRIORITY

Replicate the exact CompareGPT-AIScientist auth flow.

### 1.1 Auth Flow Summary

```
User clicks "Sign In"
  → Browser redirects to: https://comparegpt.io/sso-redirect?redirect=https://orche.platformai.org/sso/callback
  → User logs in on CompareGPT SSO
  → SSO redirects back: https://orche.platformai.org/sso/callback?token=<sso_token>
  → Frontend extracts sso_token from URL
  → Frontend calls: POST /api/user/validate { sso_token: "<sso_token>" }
  → Backend calls: POST https://auth.comparegpt.io/sso/validate (Authorization: Bearer <sso_token>)
  → SSO returns: { data: { valid: true, user_info: {...}, balance: {...}, api_key: "..." } }
  → Backend stores user in DB, generates JWT (HS256, 7-day expiry, jti for replay prevention)
  → Backend returns: { success: true, access_token: "JWT...", user: {...} }
  → Frontend stores access_token in localStorage key "access_token"
  → All subsequent API calls include: Authorization: Bearer <access_token>
```

### 1.2 Backend Changes

#### 1.2.1 Add TokenManager (`backend/core/token_manager.py`) — NEW FILE

```python
# Exact copy of CompareGPT pattern
- HS256 algorithm
- 7-day expiration
- Payload: { user_id, exp, iat, jti (secrets.token_urlsafe(16)) }
- create_access_token(user_id) → str
- verify_access_token(token) → Optional[int]
- Singleton: token_manager = TokenManager(settings.SECRET_KEY)
```

#### 1.2.2 Update AuthService (`backend/services/auth_service.py`)

```python
# Mode 1: exchange_sso_token(sso_token)
1. POST https://auth.comparegpt.io/sso/validate
   Headers: Authorization: Bearer <sso_token>
2. Validate response: data.valid == true, user_info exists, api_key exists
3. repo.upsert_user(data, sso_token, api_key)
4. token_manager.create_access_token(user_id) → JWT
5. Return { success, access_token, user: { user_info, balance, api_key } }

# Mode 2: validate_access_token(authorization)
1. token_manager.verify_access_token(token) → user_id
2. repo.get_user(user_id) → user record
3. (Optional) Refresh from SSO: POST sso_validate with stored sso_token
4. Return { success, valid, user }

# Dependency: get_current_user_id(authorization) → int
- Extract Bearer token → verify → return user_id
- Raise 401 with require_reauth: true on failure
```

#### 1.2.3 Update User Router (`backend/routers/user.py`)

```python
POST /api/user/validate
  - Body has sso_token → Mode 1 (exchange)
  - Header has Bearer token → Mode 2 (validate)
  - Neither → 400 error

POST /api/user/logout
  - Verify token → clear sso_token + api_key from DB
  - Return { success: true }
```

#### 1.2.4 Update DB Models (`backend/db/models.py`)

```python
# UserModel fields (match CompareGPT exactly):
- user_id: int (PK, from SSO)
- user_name: str
- role: str
- credit: int
- token: int
- sso_token: str (stored for refresh)
- api_key: str (stored for backend API calls)
- created_at, updated_at
```

#### 1.2.5 Update Repository (`backend/db/repo.py`)

```python
# Add methods:
- upsert_user(user_data, sso_token, api_key) → dict
- get_user(user_id) → dict with sso_token, api_key, balance
- clear_user_data(user_id) → bool (set sso_token=None, api_key=None)
```

#### 1.2.6 Update Target Router (`backend/routers/target.py`)

```python
# All target endpoints require auth:
- Use Depends(get_current_user_id) on all routes
- Remove DEFAULT_USER_ID fallback
- Scope all queries by user_id
```

#### 1.2.7 Update Config (`backend/core/config.py`)

```python
SSO_VALIDATE_URL = "https://auth.comparegpt.io/sso/validate"
ACCESS_TOKEN_EXPIRE_DAYS = 7
```

#### 1.2.8 Update .env

```env
SSO_VALIDATE_URL=https://auth.comparegpt.io/sso/validate
SECRET_KEY=<generate-real-secret>
```

### 1.3 Frontend Changes

#### 1.3.1 Add Config (`frontend/src/config/index.ts`) — NEW FILE

```typescript
export const config = {
  ssoUrl: 'https://comparegpt.io/sso-redirect?redirect=https://orche.platformai.org/sso/callback',
  logoutUrl: 'https://comparegpt.io/chat',
}
```

#### 1.3.2 Add .env Files

```env
# frontend/.env
VITE_SSO_URL=https://comparegpt.io/sso-redirect?redirect=https://orche.platformai.org/sso/callback
VITE_LOGOUT_URL=https://comparegpt.io/chat
```

#### 1.3.3 Add UserService (`frontend/src/services/user.ts`) — NEW FILE

```typescript
# Match CompareGPT exactly:
- localStorage key: "access_token"
- initiateLogin() → redirect to SSO URL
- handleOAuthCallback(ssoToken) → POST /api/user/validate { sso_token } → store token
- validateToken() → POST /api/user/validate {} with Bearer header
- logout() → POST /api/user/logout → clear localStorage
- isAuthenticated() → check localStorage
- get/set/clear AccessToken
- get/set/clear CachedUserProfile
```

#### 1.3.4 Update API Service (`frontend/src/services/api.ts`)

```typescript
# localStorage key: "access_token" (match CompareGPT)
# Auto-inject Authorization: Bearer <token> on all requests
# Handle 401 responses with require_reauth flag
```

#### 1.3.5 Update Auth Store (`frontend/src/stores/auth.ts`)

```typescript
# Match CompareGPT Pinia store:
- state: user, isAuthenticated, isLoading, error
- getters: isLoggedIn, userName, creditEnough, userRole
- actions: initialize(), handleOAuthCallback(), login(), logout()
- initialize() calls userService.validateToken() if token exists
- handleOAuthCallback() handles require_reauth with 2s delay then retry
```

#### 1.3.6 Update Router (`frontend/src/router/index.ts`)

```typescript
# Restore auth guards:
- meta: { requiresAuth: true } on dashboard and target-detail
- meta: { requiresAuth: false } on sso-callback
- beforeEach: initialize auth on first navigation (skip for callback)
- If not authenticated → authStore.login() (redirect to SSO)
```

#### 1.3.7 Update SSO Callback View (`frontend/src/views/SSOCallbackView.vue`)

```typescript
# Match CompareGPT exactly:
- 15s safety timeout
- Extract token from: query.token || query.access_token
- Handle query.error
- Show loading spinner during auth
- Show error UI with retry button on failure
- Redirect to / on success
```

#### 1.3.8 Update AppHeader (`frontend/src/components/AppHeader.vue`)

```
- Show username + role when logged in
- Show credit/token balance
- Logout button
```

### 1.4 Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/core/token_manager.py` | CREATE | JWT token manager (HS256, 7-day, jti) |
| `backend/services/auth_service.py` | REWRITE | Full SSO exchange + token validation + refresh |
| `backend/routers/user.py` | REWRITE | /validate (dual mode) + /logout |
| `backend/routers/target.py` | MODIFY | Add Depends(get_current_user_id) to all routes |
| `backend/db/models.py` | MODIFY | Add credit, token, api_key to UserModel |
| `backend/db/repo.py` | MODIFY | Add upsert_user, clear_user_data |
| `backend/core/config.py` | MODIFY | SSO_VALIDATE_URL, ACCESS_TOKEN_EXPIRE_DAYS |
| `frontend/src/config/index.ts` | CREATE | SSO URL, logout URL config |
| `frontend/src/services/user.ts` | CREATE | UserService (login, callback, validate, logout) |
| `frontend/src/services/api.ts` | MODIFY | Use "access_token" key, handle 401 |
| `frontend/src/stores/auth.ts` | REWRITE | Match CompareGPT auth store |
| `frontend/src/router/index.ts` | MODIFY | Restore auth guards with initialize() |
| `frontend/src/views/SSOCallbackView.vue` | REWRITE | Match CompareGPT callback |
| `frontend/src/components/AppHeader.vue` | MODIFY | Show user info, balance, logout |
| `frontend/.env` | CREATE | VITE_SSO_URL, VITE_LOGOUT_URL |
| `.env` | MODIFY | SSO_VALIDATE_URL, SECRET_KEY |

---

## Phase 2: Target CRUD Hardening

### 2.1 Backend

- All target routes protected by `Depends(get_current_user_id)`
- Remove `DEFAULT_USER_ID` fallback
- Scope all DB queries by authenticated `user_id`
- Soft delete (status → "archived") instead of hard delete
- Input validation: title required, maturity_level 0–5, priority in allowed list
- Rate limiting: max 100 targets per user

### 2.2 Frontend

- Loading states on all API calls
- Error toast notifications
- Optimistic UI updates with rollback on error
- Confirm dialog before delete
- Form validation on CreateTargetModal

---

## Phase 3: Maturity Pipeline Enhancement

### 3.1 Backend

| Endpoint | Description |
|----------|-------------|
| `POST /api/targets/{id}/advance` | Advance maturity (validate exit criteria) |
| `GET /api/pipeline/summary` | KPIs + distribution |
| `GET /api/pipeline/bottlenecks` | Targets stuck longest at each level |
| `GET /api/pipeline/velocity` | Avg days per maturity transition |

### 3.2 Maturity Transition Rules

```
L0 → L1: Benchmarks must be defined (at least 1), baseline value recorded
L1 → L2: current_score >= 50% of target_score
L2 → L3: current_score >= 80% of target_score, all benchmarks have values
L3 → L4: current_score >= 90% of target_score, success_criteria defined
L4 → L5: current_score >= 95% of target_score, stable for 30 days
```

### 3.3 Frontend

- Full-screen Kanban pipeline view (drag-and-drop between levels)
- Transition validation modal (shows unmet criteria)
- Bottleneck indicators (targets stuck > threshold)
- Velocity sparklines per level

---

## Phase 4: Benchmark History & Analytics

### 4.1 Backend

| Endpoint | Description |
|----------|-------------|
| `POST /api/targets/{id}/benchmarks` | Add benchmark |
| `PUT /api/targets/{id}/benchmarks/{bid}` | Record new value |
| `GET /api/targets/{id}/benchmarks/history` | Time-series values |

### 4.2 Database

```sql
benchmark_history:
  id, benchmark_id, value, recorded_at
  Index: (benchmark_id, recorded_at DESC)
```

### 4.3 Frontend

- Benchmark trend line charts (sparklines on cards, full charts on detail)
- Score progress animation
- Benchmark comparison across targets

---

## Phase 5: Resource Governance

### 5.1 Backend

| Endpoint | Description |
|----------|-------------|
| `POST /api/targets/{id}/resources` | Allocate resource |
| `PUT /api/targets/{id}/resources/{rid}` | Update consumed |
| `POST /api/targets/{id}/resources/alert` | Set alert threshold |
| `GET /api/targets/{id}/resources/usage` | Consumption report |

### 5.2 Budget Enforcement

```
- alert_at threshold: send notification (50%, 80%, 95%)
- hard_limit: auto-pause target, set status = "paused"
- RoCS calculation: maturity_gain / normalized_cost
```

### 5.3 Frontend

- Resource burn-down chart per target
- Budget alert badges on target cards
- RoCS leaderboard (highest ROI targets)
- Resource allocation modal

---

## Phase 6: Orchestration Loop Integration

### 6.1 Backend

| Endpoint | Description |
|----------|-------------|
| `POST /api/targets/{id}/dispatch` | Send to orchestration loop |
| `GET /api/targets/{id}/tasks` | Tasks linked to target |
| `POST /api/targets/{id}/capabilities` | Declare required capabilities |

### 6.2 Orchestration Loop (per PRD)

```
PERCEIVE → read target context (score, benchmarks, resources)
PLAN     → decompose into task DAG using success_criteria
PERMIT   → request capability approvals (fs.read, proc.exec, net.egress)
ACT      → execute via tool router (Claude Code / Codex / OpenClaw)
VERIFY   → re-evaluate benchmark scores
LOG      → immutable audit event
REFLECT  → advance maturity if criteria met
```

### 6.3 Capability Model

```
fs.read    → scoped by path
fs.write   → scoped by path
proc.exec  → scoped by command pattern
net.egress → scoped by domain
secrets.read → scoped by secret name
```

### 6.4 Frontend

- Dispatch button on target detail page
- Capability approval modal (Allow once / Allow for task / Deny)
- Live task execution feed
- Task results → benchmark score updates

---

## Phase 7: Audit & Compliance

### 7.1 Backend

| Endpoint | Description |
|----------|-------------|
| `GET /api/targets/{id}/audit` | Audit trail for target |
| `GET /api/audit/export` | Export CSV/JSON |

### 7.2 Immutable Audit Log

```
Every action recorded:
- target.created / target.updated / target.deleted
- maturity.advanced (from L→ to L→)
- benchmark.recorded
- resource.allocated / resource.consumed
- task.dispatched / task.completed / task.failed
- capability.granted / capability.denied

Chain-hashing: each event includes hash of previous event
```

### 7.3 Frontend

- Audit timeline on target detail page
- Exportable audit report
- Filter by event type, date range

---

## Phase 8: Hardening & Scale

### 8.1 Database Migration

- SQLite → PostgreSQL for concurrent access
- Row-level security via user_id scoping
- Connection pooling

### 8.2 Reliability

- Pre-task snapshots with restore
- Graceful degradation when SSO unavailable (use cached data)
- Rate limiting per user (100 req/min)
- Request validation & sanitization

### 8.3 Monitoring

- Health check: `/api/system/health`
- SLO dashboard (latency p95, error rate, uptime)
- Structured logging with request tracing
- Alert on: high error rate, DB connection failures, SSO timeouts

---

## File Structure (Final)

```
targeting_sys/
├── backend/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── token_manager.py          ← NEW
│   ├── db/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── repo.py
│   ├── routers/
│   │   ├── user.py
│   │   ├── target.py
│   │   └── system.py
│   ├── services/
│   │   └── auth_service.py
│   └── data/
├── frontend/
│   ├── .env                           ← NEW
│   ├── src/
│   │   ├── config/
│   │   │   └── index.ts              ← NEW
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── user.ts               ← NEW
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   └── targeting.ts
│   │   ├── views/
│   │   │   ├── DashboardView.vue
│   │   │   ├── TargetDetailView.vue
│   │   │   └── SSOCallbackView.vue
│   │   ├── components/
│   │   │   ├── AppHeader.vue
│   │   │   ├── MaturityPipeline.vue
│   │   │   ├── TargetCard.vue
│   │   │   ├── MetricsPanel.vue
│   │   │   └── CreateTargetModal.vue
│   │   ├── types/index.ts
│   │   ├── router/index.ts
│   │   └── assets/main.css
│   └── dist/
├── .env
├── ecosystem.config.js
├── nginx.conf
├── requirements.txt
├── start.sh
├── README.md
├── TARGETING_SYSTEM_PLAN.md
└── PLAN.md                            ← THIS FILE
```

---

## Implementation Order

| Step | Phase | Est. | Priority |
|------|-------|------|----------|
| 1 | Phase 1: Auth (backend token_manager + auth_service) | 1 day | P0 |
| 2 | Phase 1: Auth (frontend user service + auth store + SSO callback) | 1 day | P0 |
| 3 | Phase 1: Auth (router guards + header + .env + test) | 0.5 day | P0 |
| 4 | Phase 2: Target CRUD hardening | 0.5 day | P0 |
| 5 | Phase 3: Maturity pipeline (transition rules + Kanban) | 2 days | P1 |
| 6 | Phase 4: Benchmark history (time-series + charts) | 2 days | P1 |
| 7 | Phase 5: Resource governance (budgets + alerts + RoCS) | 2 days | P1 |
| 8 | Phase 6: Orchestration loop (dispatch + capabilities + tools) | 3 days | P2 |
| 9 | Phase 7: Audit trail (immutable log + export) | 1 day | P2 |
| 10 | Phase 8: Hardening (PostgreSQL + RLS + monitoring) | 2 days | P3 |

---

## SSO Configuration Reference

### Production URLs

```
# Frontend
SSO Login:    https://comparegpt.io/sso-redirect?redirect=https://orche.platformai.org/sso/callback
Logout:       https://comparegpt.io/chat

# Backend
SSO Validate: https://auth.comparegpt.io/sso/validate
```

### SSO Validate Request/Response

```
REQUEST:
  POST https://auth.comparegpt.io/sso/validate
  Headers: Authorization: Bearer <sso_token>

RESPONSE (200):
  {
    "data": {
      "valid": true,
      "user_info": {
        "user_id": 123,
        "user_name": "alice",
        "role": "admin"
      },
      "balance": {
        "credit": 100,
        "token": 50
      },
      "api_key": "api_key_xxx"
    }
  }
```

### JWT Token Structure

```
Algorithm: HS256
Expiry: 7 days
Payload: {
  "user_id": 123,
  "exp": <timestamp>,
  "iat": <timestamp>,
  "jti": <random_16_chars>   // replay prevention
}
```

### localStorage Keys

```
"access_token"  → JWT access token
"user_profile"  → cached user JSON
```
