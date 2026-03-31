# Auto Gold Bot (SMC Based) - Project Scaffold

This is the starter scaffold for a **private, admin-managed, multi-account MT5 trading platform** focused on **XAUUSD** and an SMC-style strategy.

## MVP direction
- **One admin dashboard**
- **Many client accounts**
- **Per-account worker process**
- **MT5 execution for trade-enabled accounts**
- **Investor access for monitor-only accounts**
- **Clear higher-timeframe trend filter**
- **Session, news, and risk controls**

## Tech stack
- **Backend API:** FastAPI + SQLAlchemy
- **Database:** PostgreSQL
- **Cache / queue (future):** Redis
- **Worker:** Python service, MT5 adapter on Windows
- **Dashboard:** Next.js + TypeScript
- **Dev environment:** VS Code
- **Containerized services:** Docker Compose (API, Postgres, Redis, dashboard)

> Note: The MT5 worker should run on **Windows** or a **Windows VPS** with the MT5 terminal installed. The rest of the stack can be developed in VS Code normally.

## Project layout
```text
apps/
  admin-dashboard/      # Next.js admin UI
services/
  api/                  # FastAPI backend
  worker/               # Strategy + execution worker
.vscode/                # VS Code launch / task config
infra/                  # Reserved for deployment scripts / IaC

docs/
  architecture.md
  mvp-scope.md
  open-questions.md
```

## Quick start
### 1) Copy env file
```bash
cp .env.example .env
```

### 2) Start local services
```bash
docker compose up --build
```

### 3) Open apps
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000

## What is already scaffolded
- FastAPI app with health route
- Basic models for clients, accounts, configs, trades, signals, users
- CRUD skeleton for clients/accounts/configs
- Worker structure with trend/risk/session/news placeholders
- Next.js admin dashboard starter page
- VS Code debug config

## What to build next
1. Finalize strict strategy definitions
2. Add Alembic migrations
3. Add real MT5 adapter
4. Add auth (admin login + worker auth)
5. Add trade execution safeguards
6. Add backtesting module
7. Add alerting and audit logs

