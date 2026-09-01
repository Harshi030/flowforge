# FlowForge

**A multi-tenant expense approval and payment workflow platform.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Ruff](https://img.shields.io/badge/code%20style-ruff-D7FF64)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)

FlowForge models how an organization reimburses employee expenses: an employee files an expense, a manager approves it, finance pays it, and every step is audited. It exists to demonstrate **production-oriented backend engineering beyond CRUD** — multi-tenancy, JWT auth, RBAC, state machines, transactions, caching, background jobs, and CI.

```
Employee files expense → Manager approves → Finance pays → Everyone notified → Everything audited
```

> **Note:** Diagrams in this README use [Mermaid](https://mermaid.js.org/) and render natively on GitHub, GitLab, and in VS Code (with the Markdown Preview Mermaid extension).

---

## Table of Contents

- [Why FlowForge](#why-flowforge)
- [Feature Highlights](#feature-highlights)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Request Lifecycle](#request-lifecycle)
- [Authentication](#authentication)
- [Multi-Tenancy](#multi-tenancy)
- [Roles & Permissions (RBAC)](#roles--permissions-rbac)
- [Redis Permission Cache](#redis-permission-cache)
- [User Invitation Workflow](#user-invitation-workflow)
- [Expense Workflow](#expense-workflow)
- [Payment Workflow](#payment-workflow)
- [Notifications & Background Jobs](#notifications--background-jobs)
- [Audit Logging](#audit-logging)
- [Pagination & Filtering](#pagination--filtering)
- [Data Layer](#data-layer)
- [Error Handling](#error-handling)
- [Security](#security)
- [API Reference](#api-reference)
- [Docker & CI](#docker--ci)
- [Development Commands](#development-commands)
- [End-to-End Flow](#end-to-end-flow)
- [Design Decisions](#design-decisions)
- [Roadmap](#roadmap)

---

## Why FlowForge

Most portfolio backends stop at CRUD. FlowForge is built around the concerns that show up in real SaaS systems:

| Concern | How FlowForge handles it |
|---|---|
| Several organizations share one database | Every tenant-owned row carries a `tenant_id`; repositories always filter on it |
| Who can do what | Granular permissions (`expense:approve`, `payment:process`, …) grouped into roles |
| Fast permission checks | Redis cache with explicit invalidation on role change |
| Invalid workflow transitions | Explicit state machines enforced in the service layer |
| Partial writes | Business change + audit log committed in a single transaction |
| Slow side effects | Email dispatched via Celery workers, never inside the request |
| Who did what, when | Tenant-scoped audit log for every state change |

---

## Feature Highlights

<table>
<tr>
<td valign="top" width="50%">

**Identity & Access**
- Multi-tenant architecture with tenant-level isolation
- JWT access + refresh tokens, refresh-token revocation
- Argon2 password hashing
- Invitation-based user onboarding (hashed, expiring, single-use tokens)
- Role-Based Access Control with granular permissions
- Redis permission cache with invalidation

</td>
<td valign="top" width="50%">

**Workflow & Operations**
- Expense lifecycle: draft → submitted → approved / rejected
- Payment lifecycle: pending → paid, one payment per expense
- Role-specific data visibility (not just endpoint protection)
- Audit logging on every state change
- Async email via Celery + Redis, Jinja2 templates, pluggable provider
- Pagination and filtering on all list endpoints

</td>
</tr>
<tr>
<td valign="top" colspan="2">

**Engineering**
- PostgreSQL + SQLAlchemy + Alembic migrations · Docker Compose · GitHub Actions CI · Ruff lint/format · Pytest

</td>
</tr>
</table>

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Language | Python 3.12 | Backend runtime |
| Web | FastAPI · Pydantic | REST API, request/response validation |
| Data | PostgreSQL · SQLAlchemy · Alembic | Relational storage, ORM, migrations |
| Cache / Broker | Redis | Permission cache and Celery broker |
| Background | Celery | Asynchronous email tasks |
| Auth | JWT · Argon2 | Tokens and password hashing |
| Email | Jinja2 | HTML email templates |
| Tooling | uv · Ruff · Pytest | Dependency management, lint/format, testing |
| Delivery | Docker · GitHub Actions | Local environment and CI |

---

## Quick Start

```bash
# 1. Clone
git clone <repository-url>
cd flowforge

# 2. Start PostgreSQL, Redis, and the Celery worker
docker compose up -d

# 3. Install backend dependencies
cd backend
uv sync

# 4. Configure environment
cat > .env <<EOF
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/flowforge
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-me
EOF

# 5. Apply migrations
uv run alembic upgrade head

# 6. Run the API
uv run uvicorn app.main:create_app --factory --reload
```

| URL | What |
|---|---|
| http://localhost:8000 | API |
| http://localhost:8000/docs | Swagger UI |

Other settings are read from environment variables — see `app/core/config.py`.

---

## Architecture

FlowForge is a **modular monolith** with a layered architecture. Each domain module (auth, tenants, users, rbac, expenses, payments, audit) owns its router → service → repository stack.

```mermaid
flowchart TB
    Client([Client])

    subgraph API["FastAPI Application"]
        Router[Routers<br/><i>HTTP concerns</i>]
        Auth[Authentication + RBAC<br/><i>dependencies</i>]
        Service[Services<br/><i>business rules, state transitions</i>]
        Repo[Repositories<br/><i>tenant-scoped queries</i>]
        Notif[Notification Service<br/><i>decides who gets notified</i>]
    end

    subgraph Infra["Infrastructure"]
        PG[(PostgreSQL)]
        Redis[(Redis<br/>cache + broker)]
        Worker[Celery Worker]
        Email[Email Service<br/><i>Jinja2 templates</i>]
        Provider[Email Provider<br/><i>Console / SMTP / …</i>]
    end

    Client --> Router --> Auth --> Service
    Service --> Repo --> PG
    Service --> Notif -->|queue task| Redis --> Worker --> Email --> Provider
    Auth <-->|permission cache| Redis
```

**Responsibilities by layer**

| Layer | Does | Does not |
|---|---|---|
| Router | Parse request, run auth dependencies, call service, map exceptions to HTTP | Contain business rules |
| Service | Validate, enforce state transitions, write audit logs, commit transactions, trigger notifications | Build SQL |
| Repository | Execute queries, always apply `tenant_id` filter | Make business decisions |
| Infrastructure | Email rendering/sending, Celery tasks | Know about expenses or payments |

---

## Project Structure

```text
flowforge/
├── docker-compose.yml
└── backend/
    ├── Dockerfile
    ├── pyproject.toml
    ├── alembic/versions/            # database migrations
    ├── tests/
    └── app/
        ├── api/health.py
        ├── core/                    # cross-cutting foundations
        │   ├── config.py            #   settings from environment
        │   ├── db.py                #   SQLAlchemy engine / session
        │   ├── redis.py             #   Redis client
        │   ├── security.py          #   JWT + Argon2 helpers
        │   └── models.py            #   shared model mixins
        ├── modules/                 # one package per domain
        │   ├── auth/                #   login, refresh, logout
        │   ├── tenants/             #   registration + approval
        │   ├── users/               #   user CRUD + invitations
        │   ├── rbac/                #   roles, permissions, seed data
        │   ├── expenses/            #   expense state machine
        │   ├── payments/            #   payment state machine
        │   ├── audit/               #   audit log read API
        │   └── notifications/       #   who-gets-notified logic
        └── infrastructure/
            ├── email/
            │   ├── provider.py      #   EmailProvider interface + ConsoleEmailProvider
            │   ├── service.py       #   template rendering
            │   └── templates/       #   *.html Jinja2 templates
            └── tasks/email_tasks.py #   Celery tasks
```

Each module in `modules/` follows the same shape:

```text
<module>/
├── router.py        # FastAPI endpoints
├── service.py       # business logic + custom exceptions
├── repository.py    # database queries
├── schemas.py       # Pydantic request/response models
├── models.py        # SQLAlchemy models
└── dependencies.py  # (auth, rbac) FastAPI dependencies
```

---

## Request Lifecycle

Every authenticated request passes through the same pipeline before reaching business logic.

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant R as Router
    participant A as Auth Dependency
    participant P as RBAC Dependency
    participant S as Service
    participant DB as Repository / PostgreSQL

    C->>R: HTTP request + Bearer JWT
    R->>A: get_current_user()
    A-->>R: user
    R->>P: requires_permission("expense:approve")
    P->>P: load permissions (Redis → PostgreSQL fallback)
    alt permission missing
        P-->>C: 403 Forbidden
    else permission present
        P-->>R: AuthContext(user, session, permissions)
        R->>S: call with AuthContext
        S->>DB: query scoped by user.tenant_id
        DB-->>S: result
        S-->>R: domain object
        R-->>C: 200 response
    end
```

The **`AuthContext`** carries `user`, `session`, and `permissions` into the service layer, which uses `user.id`, `user.tenant_id`, and `permissions` to apply business and authorization rules.

---

## Authentication

FlowForge uses JWT with a short-lived **access token** and a long-lived **refresh token**.

```mermaid
sequenceDiagram
    participant U as User
    participant API as FlowForge API
    participant DB as PostgreSQL

    U->>API: POST /auth/login (email, password)
    API->>DB: load user, verify Argon2 hash
    API-->>U: access token + refresh token
    Note over U,API: Access token sent as<br/>Authorization: Bearer <token>

    U->>API: request with expired access token
    API-->>U: 401
    U->>API: POST /auth/refresh (refresh token)
    API->>DB: verify refresh-token hash, check not revoked
    API-->>U: new access token

    U->>API: POST /auth/logout
    API->>DB: revoke refresh token
```

| Token | Lifetime | Stored | Purpose |
|---|---|---|---|
| Access | Short | Client only | Authenticate API requests |
| Refresh | Long | Hashed in DB | Mint new access tokens; can be revoked |

Passwords are never stored in plain text — only Argon2 hashes.

---

## Multi-Tenancy

Each tenant is a separate organization. All tenant-owned tables (`users`, `expenses`, `payments`, `audit_logs`) carry a `tenant_id`.

```mermaid
flowchart LR
    U[Authenticated user] --> T["auth.user.tenant_id"]
    T --> S[Service passes tenant_id]
    S --> R["Repository<br/>WHERE tenant_id = :current_tenant"]
    R --> DB[(PostgreSQL)]
```

Repositories expose tenant-aware lookups, so a user can't reach another tenant's data by guessing an ID:

```python
expense_repository.get_by_id_and_tenant(
    expense_id=expense_id,
    tenant_id=auth.user.tenant_id,
)
```

```mermaid
flowchart TB
    subgraph A["Tenant A"]
        UA[User A] --- EA[Expense A] --- PA[Payment A]
    end
    subgraph B["Tenant B"]
        UB[User B] --- EB[Expense B] --- PB[Payment B]
    end
    UA -. "❌ cannot access" .-> EB
```

---

## Roles & Permissions (RBAC)

Authorization is permission-based; roles are just named bundles of permissions.

```mermaid
erDiagram
    USER ||--o{ USER_ROLE : has
    ROLE ||--o{ USER_ROLE : assigned_in
    ROLE ||--o{ ROLE_PERMISSION : grants
    PERMISSION ||--o{ ROLE_PERMISSION : included_in
```

### Permission Matrix

| Permission | ADMIN | MANAGER | FINANCE | EMPLOYEE |
|---|:-:|:-:|:-:|:-:|
| `expense:create` | ✅ | ✅ | | ✅ |
| `expense:read` | ✅ | ✅ | | ✅ |
| `expense:read:all` | ✅ | ✅ | | |
| `expense:read:approved` | | | ✅ | |
| `expense:approve` | ✅ | ✅ | | |
| `expense:reject` | ✅ | ✅ | | |
| `payment:create` | ✅ | | ✅ | |
| `payment:read` | ✅ | | ✅ | |
| `payment:process` | ✅ | | ✅ | |
| `user:create` | ✅ | | | |
| `user:manage` | ✅ | | | |
| `role:manage` | ✅ | | | |
| `audit:read` | ✅ | | | |

### Role Summary

| Role | Responsibility |
|---|---|
| **ADMIN** | Full access — user management, RBAC, expenses, payments, audit logs |
| **MANAGER** | Create expenses, see all tenant expenses, approve / reject |
| **FINANCE** | See approved expenses, create / view / process payments. Cannot approve or reject |
| **EMPLOYEE** | Create and view own expenses only |

### Enforcing Permissions

Endpoints declare what they need via a dependency:

```python
@router.post("/{expense_id}/approve")
def approve_expense(
    expense_id: UUID,
    auth: AuthContext = Depends(requires_permission("expense:approve")),
):
    ...
```

### Permissions Shape Data, Not Just Endpoints

The same permissions control *which rows* a user sees on `GET /expenses`:

```mermaid
flowchart LR
    Q["GET /api/v1/expenses"] --> D{Which permission?}
    D -->|"expense:read:all"| M["All tenant expenses<br/>(Manager, Admin)"]
    D -->|"expense:read:approved"| F["Only status = approved<br/>(Finance)"]
    D -->|"expense:read"| E["Only own expenses<br/>(Employee)"]
```

This lets Finance work on what's ready to pay without seeing the rest of the workflow — least privilege applied to data visibility.

---

## Redis Permission Cache

Resolving `User → UserRole → Role → RolePermission → Permission` on every request is wasteful, so permissions are cached in Redis under `rbac:permissions:user:{user_id}` with a TTL.

```mermaid
flowchart TB
    Req[Request] --> L[Permission lookup]
    L --> C{Redis hit?}
    C -->|yes| Ret[Return permissions]
    C -->|no| PG[(PostgreSQL join)]
    PG --> Store[Store in Redis with TTL]
    Store --> Ret

    RC[Role change] -->|"DELETE rbac:permissions:user:{id}"| Redis[(Redis)]
    Redis -. next request misses .-> PG
```

Invalidation is explicit: when a user's roles change, the key is deleted and the next lookup rebuilds it from PostgreSQL. Result: fast reads **and** correct permissions immediately after a role change.

---

## User Invitation Workflow

Users don't self-register. An admin creates them, and they activate via a one-time invitation.

```mermaid
sequenceDiagram
    participant Admin
    participant API
    participant DB
    participant Worker as Celery
    participant User

    Admin->>API: POST /users
    API->>DB: create user (inactive)
    API->>API: generate random token, hash it
    API->>DB: store invitation (token_hash, expires_at, used_at=null)
    API->>Worker: queue invitation email
    Worker-->>User: email with raw token
    User->>API: accept invitation (token, password)
    API->>API: validate: exists · not used · not expired · user exists
    API->>DB: set password hash, mark used_at, activate user
    API-->>User: active account
```

**Token safety:** the raw token is only ever in the email. The database holds a hash, an expiry, and a `used_at` marker — so a leaked database can't be used to accept invitations, and each token works exactly once.

---

## Expense Workflow

Expenses follow an explicit state machine. The service layer rejects any transition not shown below (e.g. `draft → approved`).

```mermaid
stateDiagram-v2
    [*] --> draft : create<br/>EXPENSE_CREATED
    draft --> submitted : submit (owner)<br/>EXPENSE_SUBMITTED
    submitted --> approved : approve (expense:approve)<br/>EXPENSE_APPROVED
    submitted --> rejected : reject (expense:reject)<br/>EXPENSE_REJECTED
    approved --> [*] : handed to payment workflow
    rejected --> [*]
```

### Transition Rules

| Transition | Required permission | Rules enforced by the service |
|---|---|---|
| create → `draft` | `expense:create` | Belongs to caller's tenant; audit `EXPENSE_CREATED` |
| `draft` → `submitted` | (owner) | Caller owns the expense · status is `draft` · sets `submitted_at` · notifies approvers |
| `submitted` → `approved` | `expense:approve` | Status is `submitted` · **cannot approve own expense** · sets `approved_at` · notifies employee + finance |
| `submitted` → `rejected` | `expense:reject` | Status is `submitted` · **cannot reject own expense** · rejection reason required and stored · notifies employee |

Every transition runs inside one transaction: update the expense, write the audit log, commit — then queue notifications.

---

## Payment Workflow

Payments exist only for approved expenses, and each expense gets at most one.

```mermaid
stateDiagram-v2
    [*] --> pending : create (payment:create)<br/>PAYMENT_CREATED
    pending --> paid : process (payment:process)<br/>PAYMENT_PAID
    paid --> [*]
```

### Payment Creation

```mermaid
flowchart TB
    S[POST /payments] --> L[Load expense by id + tenant]
    L --> E{Exists?} -->|no| N404[404]
    E -->|yes| A{status == approved?} -->|no| B400[400]
    A -->|yes| D{Payment already exists?} -->|yes| C409[409]
    D -->|no| Cr["Create payment<br/>copy amount + currency from expense"]
    Cr --> Au[Audit PAYMENT_CREATED] --> Cm[Commit]
```

### Duplicate Protection — Two Layers

| Layer | Mechanism |
|---|---|
| Service | Checks for an existing payment before creating |
| Database | `UNIQUE` constraint on `payments.expense_id` |

The service check gives a clean 409; the constraint guarantees correctness even under concurrent requests.

### Payment Record

| Field | Notes |
|---|---|
| `expense_id` | FK to the approved expense, unique |
| `amount`, `currency` | **Snapshot** copied from the expense at creation time |
| `status` | `pending` → `paid` |
| `paid_at` | Set on processing |
| `created_by`, `updated_by`, `created_at`, `updated_at` | Via shared mixins |

---

## Notifications & Background Jobs

Email is a side effect, not part of the request. The API queues a task and returns; a Celery worker does the sending.

```mermaid
flowchart LR
    BS[Business service<br/>e.g. approve_expense] --> NS[Notification service<br/>resolves recipients]
    NS -->|"task.delay(...)"| Broker[(Redis broker)]
    Broker --> W[Celery worker]
    W --> ES[Email service<br/>renders Jinja2 template]
    ES --> EP[EmailProvider]
    EP --> Console[ConsoleEmailProvider<br/><i>dev</i>]
    EP --> Prod[Production provider<br/><i>future</i>]
```

### Who Gets Notified

| Event | Recipients | Template |
|---|---|---|
| Expense submitted | Every user with `expense:approve` | `expense_submitted.html` |
| Expense approved | Employee **and** Finance users | `expense_approved.html`, `expense_ready_for_payment.html` |
| Expense rejected | Employee | `expense_rejected.html` |
| Payment paid | Employee | `payment_paid.html` |

Templates receive recipient name, employee name, amount, currency, description, and rejection reason where applicable.

### Provider Abstraction

```python
class EmailProvider(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html: str) -> None: ...
```

Swapping `ConsoleEmailProvider` for a real provider (SES, SendGrid, SMTP) touches only infrastructure — business code is unaffected.

---

## Audit Logging

Every state-changing operation writes a tenant-scoped audit row **in the same transaction** as the change.

```mermaid
flowchart LR
    subgraph TX["One transaction"]
        U[Update entity] --> A[Insert audit log]
    end
    TX --> C{Commit OK?}
    C -->|yes| Done[Both persisted]
    C -->|no| RB[Rollback — neither persisted]
```

**Recorded actions**

| Users | Expenses | Payments |
|---|---|---|
| `USER_CREATED` | `EXPENSE_CREATED` | `PAYMENT_CREATED` |
| `USER_UPDATED` | `EXPENSE_SUBMITTED` | `PAYMENT_PAID` |
| `USER_ROLE_CHANGED` | `EXPENSE_APPROVED` | |
| `USER_ACTIVATED` | `EXPENSE_REJECTED` | |
| `USER_DEACTIVATED` | | |

**Audit row example**

```json
{
  "tenant_id": "…",
  "user_id": "…",
  "action": "EXPENSE_APPROVED",
  "entity_type": "expense",
  "entity_id": "…",
  "details": { "previous_status": "submitted", "new_status": "approved" },
  "created_at": "2026-09-01T10:15:00Z"
}
```

Audit reads require `audit:read` and are filtered by `tenant_id` like everything else.

---

## Pagination & Filtering

All list endpoints (users, expenses, payments, audit logs) are paginated:

```
GET /api/v1/expenses?page=2&page_size=20      →  offset = (page - 1) * page_size
```

```json
{
  "items": [],
  "page": 2,
  "page_size": 20,
  "total": 100,
  "total_pages": 5
}
```

| Endpoint | Filters |
|---|---|
| Audit logs | `action`, `entity_type`, `user_id` |
| Payments | `status` |
| Expenses | Implicit, by permission (see [RBAC](#permissions-shape-data-not-just-endpoints)) |

---

## Data Layer

### Models

Shared columns come from reusable mixins in `core/models.py`, keeping every model consistent:

| Mixin | Provides |
|---|---|
| `UUIDPrimaryKeyMixin` | `id: UUID` |
| `TimestampMixin` | `created_at`, `updated_at` |
| `CreatedByMixin` | `created_by` |
| `UpdatedByMixin` | `updated_by` |

### Core Entities

```mermaid
erDiagram
    TENANT ||--o{ USER : has
    TENANT ||--o{ EXPENSE : owns
    TENANT ||--o{ PAYMENT : owns
    TENANT ||--o{ AUDIT_LOG : owns
    USER ||--o{ EXPENSE : creates
    USER ||--o| INVITATION : receives
    USER }o--o{ ROLE : assigned
    ROLE }o--o{ PERMISSION : grants
    EXPENSE ||--o| PAYMENT : "paid by (unique)"
    USER ||--o{ AUDIT_LOG : performs
```

### Migrations

```bash
uv run alembic revision --autogenerate -m "describe change"   # create
uv run alembic upgrade head                                    # apply
```

### Transactions

State-changing service methods use an explicit commit/rollback pattern so an operation is all-or-nothing:

```python
try:
    expense.status = ExpenseStatus.APPROVED
    expense.approved_at = now()
    audit_repository.create(...)
    session.commit()
except Exception:
    session.rollback()
    raise
```

---

## Error Handling

Services raise domain exceptions; routers translate them into HTTP responses. Business code never imports `HTTPException`.

```mermaid
flowchart LR
    S[Service raises] --> NF[ExpenseNotFoundError<br/>PaymentNotFoundError] --> R404[404 Not Found]
    S --> IS[InvalidExpenseStateError<br/>InvalidPaymentStateError] --> R400[400 Bad Request]
    S --> SA[ExpenseSelfApprovalError] --> R403[403 Forbidden]
    S --> DP[Duplicate payment] --> R409[409 Conflict]
```

| Situation | Status |
|---|---|
| Resource not found (or belongs to another tenant) | `404` |
| Invalid state transition | `400` |
| Missing permission / self-approval | `403` |
| Duplicate resource | `409` |

Not-found and cross-tenant both return `404` — the API never reveals that a resource exists in another tenant.

---

## Security

| Area | Control |
|---|---|
| Passwords | Argon2 hashing, never stored in plain text |
| Tokens | Short-lived access JWT · long-lived hashed refresh token · revocation on logout · expiry on both |
| Invitations | Random token · only the hash stored · expiring · single-use |
| Authorization | Granular permissions on every mutating endpoint |
| Tenant isolation | `tenant_id` filter in every repository query |
| Business rules | No self-approval / self-rejection · state-guarded transitions · one payment per expense (service + DB constraint) |

---

## API Reference

All routes are prefixed with `/api/v1`.

### Auth
| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Exchange credentials for access + refresh tokens |
| `POST` | `/auth/refresh` | Issue a new access token |
| `POST` | `/auth/logout` | Revoke refresh token |

### Tenant Registration
| Method | Path | Description |
|---|---|---|
| `POST` | `/registration/register` | Register a new tenant |
| `GET` | `/registration/approve` | Approve a pending tenant |

### Users
| Method | Path | Permission |
|---|---|---|
| `POST` | `/users` | `user:create` |
| `GET` | `/users` | `user:manage` |
| `GET` | `/users/{user_id}` | `user:manage` |
| `PATCH` | `/users/{user_id}` | `user:manage` |

### Expenses
| Method | Path | Permission |
|---|---|---|
| `POST` | `/expenses` | `expense:create` |
| `GET` | `/expenses` | `expense:read` / `:read:all` / `:read:approved` (shapes results) |
| `GET` | `/expenses/{expense_id}` | `expense:read` |
| `POST` | `/expenses/{expense_id}/submit` | owner |
| `POST` | `/expenses/{expense_id}/approve` | `expense:approve` |
| `POST` | `/expenses/{expense_id}/reject` | `expense:reject` |

### Payments
| Method | Path | Permission |
|---|---|---|
| `POST` | `/payments` | `payment:create` |
| `GET` | `/payments` | `payment:read` |
| `GET` | `/payments/{payment_id}` | `payment:read` |
| `POST` | `/payments/{payment_id}/pay` | `payment:process` |

### Audit
| Method | Path | Permission |
|---|---|---|
| `GET` | `/audit/audit-logs` | `audit:read` |

Interactive docs: `http://localhost:8000/docs`

---

## Docker & CI

### Local services

```mermaid
flowchart LR
    API[FastAPI API] --> PG[(PostgreSQL)]
    API --> R[(Redis)]
    R --> W[Celery Worker]
```

`docker compose up -d` brings up PostgreSQL, Redis, and the Celery worker. Redis serves double duty as permission cache and task broker.

### Continuous Integration

GitHub Actions runs on every push to `master` and on pull requests:

```mermaid
flowchart LR
    Push[Push / PR] --> Co[Checkout] --> Py[Python 3.12] --> UV[Install uv] --> Dep[uv sync]
    Dep --> Lint[ruff check]
    Dep --> Fmt[ruff format --check]
    Dep --> Test[pytest]
```

CI injects `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET` as environment configuration.

---

## Development Commands

| Task | Command |
|---|---|
| Run API (hot reload) | `uv run uvicorn app.main:create_app --factory --reload` |
| Run tests | `uv run pytest -v` |
| Lint | `uv run ruff check app tests` |
| Lint + auto-fix | `uv run ruff check app tests --fix` |
| Format check | `uv run ruff format --check app tests` |
| Format | `uv run ruff format app tests` |
| New migration | `uv run alembic revision --autogenerate -m "…"` |
| Apply migrations | `uv run alembic upgrade head` |

---

## End-to-End Flow

From an empty system to a paid reimbursement:

```mermaid
flowchart TB
    subgraph Setup["1 · Tenant setup"]
        T1[Tenant registers] --> T2[Tenant approved] --> T3[Admin logs in]
        T3 --> T4[Admin creates users] --> T5[Invitations sent] --> T6[Users accept, set password, activate]
    end

    subgraph Expense["2 · Expense"]
        E1[Employee creates expense<br/><b>draft</b>] --> E2[Employee submits<br/><b>submitted</b>]
        E2 --> E3[Approvers notified] --> E4{Manager decision}
        E4 -->|approve| E5[<b>approved</b><br/>employee + finance notified]
        E4 -->|reject| E6[<b>rejected</b><br/>employee notified]
    end

    subgraph Payment["3 · Payment"]
        P1[Finance views approved expenses] --> P2[Finance creates payment<br/><b>pending</b>]
        P2 --> P3[Finance processes payment<br/><b>paid</b>] --> P4[Employee notified]
    end

    Setup --> Expense
    E5 --> Payment

    Audit[(Audit log<br/>every state change)]
    T4 -.-> Audit
    E1 -.-> Audit
    E2 -.-> Audit
    E5 -.-> Audit
    E6 -.-> Audit
    P2 -.-> Audit
    P3 -.-> Audit
```

<details>
<summary>Step-by-step (25 steps)</summary>

1. Tenant registers
2. Tenant is approved
3. Admin logs in
4. Admin creates employee, manager, and finance users
5. Invitations are generated
6. Users accept invitations
7. Users set passwords
8. Users become active
9. Employee logs in
10. Employee creates an expense
11. Expense starts in `draft`
12. Employee submits the expense
13. Expense becomes `submitted`
14. Users with `expense:approve` are notified
15. Manager reviews the expense
16. Manager approves or rejects it
17. If rejected, employee is notified
18. If approved, employee and Finance are notified
19. Finance views approved expenses
20. Finance creates a payment
21. Payment starts as `pending`
22. Finance processes the payment
23. Payment becomes `paid`
24. Employee receives payment notification
25. Every step above is in the audit log

</details>

---

## Design Decisions

| Decision | Why |
|---|---|
| **Router → Service → Repository** | HTTP, business rules, and SQL each have one home. Services are testable without FastAPI; repositories are the single place tenant filtering lives. |
| **Business logic in services, not routers** | Routers only parse, authorize, call, and respond. State transitions, audit, notifications, and transactions are service concerns. |
| **Permissions, not role checks** | Endpoints depend on `expense:approve`, never on "is manager". Roles can be reshaped without touching endpoints. |
| **Least privilege by default** | Finance gets `expense:read:approved` rather than `expense:read:all`. Employees can't approve anything. |
| **Explicit state machines** | Invalid transitions (`draft → approved`) are rejected in code, not left to convention. |
| **Cache with invalidation, not just TTL** | Role changes delete the Redis key immediately, so a demoted user loses access on their next request. |
| **Email is asynchronous** | Delivery time and provider outages must not affect API latency or correctness. |
| **Change + audit in one transaction** | An audit row without its change, or a change without its audit row, is never possible. |
| **Snapshot amount on payment** | The payment records what was actually paid, even if the expense were later edited. |
| **Defense in depth on duplicates** | Service check for a friendly 409 plus a DB unique constraint for a hard guarantee. |

---

## Roadmap

- [ ] Production email provider integration
- [ ] Email retry policies and dead-letter handling
- [ ] Structured application logging
- [ ] Metrics and monitoring
- [ ] Additional integration tests
- [ ] Payment provider integration
- [ ] Rate limiting
- [ ] Cloud deployment and CI/CD pipeline
- [ ] Reporting, analytics, and dashboards

---

<p align="center"><sub>FlowForge — authentication · authorization · multi-tenancy · RBAC · workflows · transactions · caching · background jobs · notifications · audit · pagination · migrations · Docker · testing · CI</sub></p>