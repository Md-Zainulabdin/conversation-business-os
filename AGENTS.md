# Conversational Business OS (CBO)

> A production-ready side project that lets small retailers run their business by talking instead of filling ERP forms.

---

# Intro

CBO is a **conversational business operating system**. The long-term vision: a shopkeeper manages sales, purchases, expenses, and stock through simple messages and voice notes rather than a dashboard of forms.

The core architectural rule: **AI only understands language — it never touches the database.**

```
User Message
      ↓
Intent Extraction
      ↓
Validation
      ↓
Business Logic
      ↓
Database
```

The AI turns free-text into a structured proposal; the backend validates it, the user confirms, and only then is anything written. Business logic always belongs in the backend.

# Description

A web app (Next.js frontend + FastAPI backend) with full retail features:

- **Secure accounts** with per-user data isolation (JWT + bcrypt).
- **Inventory**: products, categories, customers, and automatic stock tracking with low-stock thresholds.
- **Transactions**: multi-item sales, purchases, and expenses — stock adjusts automatically, with integrity guards on create/edit/delete.
- **Dashboard**: total sales, stock, customers, and a searchable recent-activity feed (24h / 7d / 30d / 12m periods).
- **AI assistant**: type plain language ("Sold 20 packs of rice") and the assistant proposes the transaction, asks for confirmation (and disambiguation when ambiguous), then records it — with idempotency and conversation memory.
- **81 passing automated tests** covering stock integrity, per-user isolation, and AI safety guardrails. CI/CD via GitHub Actions.

---

# Current Portfolio Plan

> Approved plan to take the project from "great progress" (Phases 0-3) to a complete, portfolio-ready, deployed application. Executed in order A → F.

## Current State

- Phase 0 (Foundation), Phase 1 (Inventory), Phase 2 (Sales), Phase 3 (AI) — **done**
- Phase 4 (WhatsApp) — **paused** (de-prioritized; pipeline is transport-agnostic so it stays an option)
- Phase 5 (Voice) — **next** (via Groq Whisper API, reusing the existing Groq key)
- Phase 6 (Reports) — **partially done** (only the dashboard overview exists)

## Phase A — Security & Repo Hygiene (½ day)

1. Remove the committed Groq API key from `apps/api/.env`. Rotate the key. Keep `.env` git-ignored; document only `.env.example`.
2. Fix `scripts/seed.py` — it still posts the old flat-body shape and fails against the current multi-item `items[]` API.
3. Enforce `is_active` in `get_current_user` (the flag exists on the model but is never checked).
4. Remove stale artifacts: orphaned code block in `tests/test_ai.py` (~line 441), outdated `.pytest_cache` entries.
5. Make dead/decorative UI real or remove it: hardcoded dashboard date-range button, non-functional header search input, decorative notification bell, and the missing client-side stock check on the sales edit page (the New form has it).

## Phase B — Reports & Analytics (Phase 6) (2-3 days)

Backend (`apps/api`):
- Extend `GET /stats/overview` (or add `/stats/reports`) to return per period: revenue vs expenses (profit), daily sales summary, low-stock alerts (products where `stock_quantity <= minimum_stock`), top-selling products, top customers, and category breakdowns.

Frontend (`apps/web`):
- Rebuild the placeholder `/reports` page with a period selector (reuse the 24h/7d/30d/12m pattern): KPI cards (Revenue, Expenses, Profit, Low-stock count), charts (revenue-vs-expense, top products, expense category pie) using **Recharts** — the only new dependency, justified by charts being the key visible win — plus a low-stock alerts list.
- Make the dashboard date-range control functional (drive the period selector).

Tests:
- Add `test_stats.py` covering profit math, low-stock thresholds, and per-user scoping of report data.

## Phase C — Voice Agent (Phase 5) (1-2 days)

Backend:
- Add `POST /ai/voice` accepting a multipart audio upload.
- Transcribe with **Groq Whisper API** (reuses the existing `GROQ_API_KEY`, e.g. `whisper-large-v3` / `distil-whisper-large-v3`).
- Feed the transcript straight into the existing `ai_service.propose()` → same confirm/execute flow. **Zero new business logic.** Reuse the same idempotency + session guards.

Frontend:
- Mic record button on the assistant chat (`MediaRecorder` → upload → transcript shown as a user bubble → normal confirmation flow).

Tests:
- Mock the transcription client; verify a voice transcript produces the same proposal/execute behavior as typed text (extend `test_ai.py`).

## Phase D — Production Hardening (2 days)

1. Move AI session history + idempotency from in-memory to **Redis** (`REDIS_URL` is already configured but unused). Safe across multiple workers.
2. Pagination on list endpoints (`limit`/`offset` or cursor) + pagination control in the shared `DataTable`.
3. Real Settings page — editable store name, currency, password change, account actions (replaces the static cards).
4. Auth + HTTP-level `TestClient` tests — currently zero tests hit the routes.
5. Notification bell → low-stock alerts from Phase B.

## Phase E — Deployment (1 day)

- Backend → **Railway**: `Dockerfile` exists. Add Neon `DATABASE_URL`, Upstash `REDIS_URL`, `GROQ_API_KEY`, `SECRET_KEY`, Whisper key to the service env. Run `alembic upgrade head` as a release command.
- Frontend → **Vercel**: connect the repo; `NEXT_PUBLIC_API_URL` pointing at the Railway URL.
- CI: add a deploy job to `.github/workflows/ci.yml` on merge to `main` (keep the existing quality job). This completes the CI/CD story from the roadmap.

## Phase F — Optional Extras (time permitting)

- Read-only detail/view pages (`/products/[id]`, `/sales/[id]`, …) — only list + edit exist today.
- Weekly report email or PDF export.
- WhatsApp integration later (the propose/execute pipeline is already transport-agnostic).

## Sequencing & Effort

| Order | Stream | Effort |
|-------|--------|--------|
| 1 | A — Security & hygiene | ½ day |
| 2 | B — Reports | 2-3 days |
| 3 | C — Voice agent | 1-2 days |
| 4 | D — Hardening | 2 days |
| 5 | E — Deployment | 1 day |
| 6 | F — Extras | time permitting |

Total ≈ 1.5 weeks. End goal: a live, deployed, voice-enabled retail management app with reports, ready to demo and link from a resume.

---

# Coding Agent Guardrails

Act as a senior software engineer and software architect on every task. Prioritize simplicity, correctness, readability, maintainability, and long-term scalability over clever or overly abstract solutions. Follow the current project phase only and never implement future features unless explicitly requested. Do not make assumptions—if requirements are ambiguous or a design decision could affect the architecture, stop and ask for clarification. Write production-quality code using established best practices, keep files organized and reasonably small, remove dead code and stale files, avoid duplication, and refactor only when there is clear value. Handle errors comprehensively on both the frontend and backend with proper validation, structured error responses, meaningful user feedback, logging, and graceful failure handling. Consider edge cases, security, performance, and maintainability as part of every implementation, and ensure that new changes do not introduce regressions.

Treat the repository as the source of truth and make only the changes required for the requested task. Never commit, push, merge, create pull requests, or perform any GitHub operations without explicit user approval. Never delete or modify existing functionality unless it is necessary for the requested change, and always explain any architectural decisions that significantly affect the codebase. Before completing a task, verify that the project builds successfully, code is formatted and linted where applicable, imports are clean, unused code has been removed, and the implementation is consistent with the project's architecture and conventions. The goal is to produce production-ready, understandable code that a single developer can confidently maintain and extend.