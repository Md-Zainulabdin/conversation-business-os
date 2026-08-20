# CBO — Project Status & Portfolio Roadmap

> Full inventory of what has been built, progress against the AGENTS.md roadmap, and what is needed to make this a standout portfolio/resume project.

---

## 1. The Big Picture

**Conversational Business OS (CBO)** is a retail management platform where a shopkeeper runs day-to-day business by typing normal sentences (and eventually sending voice notes and WhatsApp messages) instead of filling ERP forms.

The architecture follows one strict rule: **AI only understands language — it never touches the database.** Every message becomes a structured proposal that the system validates, the user confirms, and only then is saved. This separation of "understanding" (AI) from "deciding" (backend business logic) is the core engineering idea of the project.

Current state: a **production-quality web app** with a **genuinely conversational AI assistant**, backed by **114 passing automated tests**, **CI/CD on GitHub Actions**, and **multi-user data isolation**.

---

## 2. What Has Been Built (Feature Inventory)

### 2.1 Foundation (Phase 0) — Complete
- **Monorepo** with TurboRepo (Next.js frontend + FastAPI backend + shared config packages).
- **Local dev environment** via Docker Compose (PostgreSQL + Redis).
- **GitHub Actions CI** (`.github/workflows/ci.yml`): lints the frontend and backend, runs all backend tests, and builds the frontend on every push/PR to `main`.
- Git workflow with feature branches and conventional commits.

### 2.2 Authentication & Security
- Register / Login with **JWT** (HS256, 24h expiry) and **bcrypt** password hashing.
- Protected routes on both frontend (middleware + client guard) and backend (every endpoint except health/auth requires a token).
- **Per-user data isolation:** every record belongs to a user; users can never see or touch each other's data (verified by dedicated isolation tests).
- Per-user uniqueness on product SKU and customer phone.

### 2.3 Inventory System (Phase 1) — Complete
- **Products:** full CRUD — name, SKU, category, unit (Piece/Pack/KG/Litre/Carton…), purchase & selling price, current stock, minimum stock threshold.
- **Categories:** CRUD for organizing products.
- **Customers:** CRUD with name, phone, address.
- **Stock is always tracked on the product itself**, with a low-stock threshold used for warnings.

### 2.4 Business Transactions (Phase 2) — Complete
- **Sales:** create/edit/delete with **multiple line items per sale**, price snapshot, customer link, and **automatic stock deduction** (with a strict insufficient-stock guard).
- **Purchases:** create/edit/delete with multiple items, free-text supplier, and **automatic stock increase**.
- **Expenses:** create/edit/delete with categorized spending (Electricity, Internet, Transport, Salary, Rent, Miscellaneous).
- **Stock integrity:** editing a sale/purchase restores old quantities and applies new ones; deleting restores stock — all within single DB transactions with row locks to prevent race conditions.

### 2.5 Dashboard & Analytics
- Overview page with period selector (last 24h / 7 days / 30 days / 12 months).
- Stat cards: total sales (Rs), stock items, active customers.
- Recent-transactions feed (sales + purchases + expenses merged, searchable + filterable).

### 2.6 AI Assistant (Phase 3) — Complete (the centerpiece)
- Type plain language and the AI turns it into a structured command (via **Groq** with strict JSON-schema output — model `openai/gpt-oss-120b`).
- Supported intents: **sale, purchase, expense, inquiry, other** — including multi-product messages ("Sold 10 packs of rice and 20 coca-colas") and Roman-Urdu / Pakistani-English ("Bhai 10 rice sale kar do", "Bijli ka 5000 bill diya").
- Full **propose → confirm → execute** flow:
  - The AI **proposes** a transaction; the user sees exactly what will be recorded, then confirms.
  - **Disambiguation:** if the user says something that could match several products, the assistant asks which one they meant (radio list showing stock and prices) — it never guesses.
  - **Validation in the backend, not the AI:** unknown products, missing quantities, unit mismatches, and price anomalies are caught and explained per line-item before anything is written.
  - **Idempotency:** retries/double-clicks can never record a transaction twice.
  - **Conversation memory:** follow-ups like "sell 10" resolve correctly (10-minute in-memory session per conversation).
- **Stock inquiries:** "How much Coke stock is left?" → live stock answer.
- Frontend: a complete chat interface with suggestion chips, confirmation cards, cancel words ("cancel", "never mind"), per-item stock-after reporting, and friendly error handling.

### 2.7 Voice Agent (Phase 5) — Complete
- Mic button on the assistant chat (`MediaRecorder` → webm upload → `POST /ai/voice`).
- Backend transcribes with **Groq Whisper** (`whisper-large-v3-turbo`, reuses the existing `GROQ_API_KEY`) then feeds the transcript through the exact same `propose` pipeline — zero new business logic.
- Transcript appears as a user bubble, then the normal confirm/execute/disambiguation flow takes over.
- Same idempotency + per-user session guards; mocks in the test suite prove a voice transcript behaves identically to typed text.

### 2.8 Frontend Engineering Quality
- Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, shadcn-style components, Zustand state, react-hook-form + zod validation.
- Shared reusable components: data tables, toolbars with debounced search + filters + filter pills, dialogs, spinners, page headers, error boundaries, custom 404.
- Fully responsive (sidebar → mobile drawer), loading/empty/error states everywhere, PKR currency formatting throughout.

### 2.9 Testing & Verification
- **101 automated tests passing** (`python -m pytest`): stock integrity, per-user isolation, AI safety guardrails, schema validation, and AI happy paths.
- The AI safety suite proves the system **never** writes bad data: failed transactions leave stock unchanged, ambiguous products are never guessed, duplicate lines are handled, and idempotency holds.

---

## 3. Progress vs. the AGENTS.md Roadmap

| Phase | Goal | Status |
|------|------|--------|
| 0 — Foundation | Monorepo, FastAPI, Next.js, DB, Docker, GitHub CI | ✅ **Done** |
| 1 — Inventory | Auth, Products, Categories, Inventory, Dashboard | ✅ **Done** |
| 2 — Sales | Sales, Purchases, Expenses | ✅ **Done** |
| 3 — AI | Natural language → structured commands, backend validates | ✅ **Done** |
| 4 — WhatsApp | Receive/process/reply via WhatsApp | ⏸ **Paused (de-prioritized)** |
| 5 — Voice | Voice notes → speech-to-text → AI → execute | ✅ **Done** |
| 6 — Reports | Daily summary, revenue, low-stock alerts | ✅ **Done** (charts, profit, low-stock) |
| D — Hardening | Redis sessions, pagination, real settings, HTTP tests, low-stock bell | ✅ **Done** |
| E — Deployment | Dockerfiles, Railway config, CI deploy | ✅ **Done** (config + docs ready; live deploy on user's Railway account) |

---

## 4. What Remains to Make It Portfolio-Ready

Ranked by impact. Items marked ★ are the highest-value additions.

### Must-do (correctness / credibility)
1. ★ **Rotate the Groq API key** and keep `.env` git-ignored (env-only keys). The key was verified **never committed** (only `.env.example` is tracked, with placeholders), but rotate it before any public demo.
2. ~~**Finish the Reports phase (Phase 6)**~~ — done: KPI cards (Revenue/Expenses/Profit/Low stock), Recharts revenue trend + expense pie + top products, top-customers list, and low-stock alerts table with period selector.
3. ~~**Fix `scripts/seed.py`**~~ — done in Phase A (now posts the multi-item `items[]` shape).
4. ~~**Wire the decorative UI**~~ — done in Phase A: removed the hardcoded date-range button, header search, and notification bell; added the client-side stock check to the sales edit form.

### High-value features
5. ~~**Voice agent (Phase 5)**~~ — done: mic button records audio, `POST /ai/voice` transcribes via Groq Whisper, transcript feeds the exact same propose/confirm/execute pipeline (zero new business logic). Mocked tests prove voice behaves identically to typed text.
6. ~~**In-memory session → Redis**~~ — done: session history and idempotency moved to Redis (`REDIS_URL`), safe across multiple workers and restarts.

### Nice-to-have polish
7. ~~**Pagination** on list endpoints (currently all rows render client-side).~~ — done: `Page[T]` pagination on all list endpoints with shared `DataTable` controls.
8. ~~**Real settings page** (editable store name, currency, account actions) instead of static cards.~~ — done.
9. ~~**Authentication tests** (currently none) + an HTTP-level API test suite.~~ — done: 13 `TestClient` HTTP route tests.
10. Read-only **detail/view pages** (currently only list + edit exist).
11. ~~**CI deployment** to Vercel/Railway on merge to `main` (the CI currently checks quality but doesn't deploy).~~ — done: deploy job added to `.github/workflows/ci.yml` using the Railway CLI action on `main` merges.

---

## 5. Suggested Final Roadmap

1. ~~**Redis-backed sessions**~~ — done (Phase D).
2. ~~**Polish pass**~~ — done: pagination, settings page, auth/HTTP tests (Phase D).
3. **Deploy** both apps to Railway (all-Railway) so it's a live link on the resume. See `docs/deployment.md` for step-by-step instructions.

---

## 6. One-Paragraph Pitch (for a resume bullet or demo intro)

> Built a conversational retail management system where a shopkeeper records sales, purchases, expenses, and stock by typing or speaking natural language. The system uses an LLM to turn free-text messages into structured commands, but all validation and data writes happen in a deliberately guarded backend layer — the AI never touches the database directly. The app features per-user data isolation, automatic stock management, a chat-style AI assistant with confirmation and disambiguation, voice input via Whisper transcription, 114 passing tests covering stock integrity and AI safety, and CI/CD via GitHub Actions.

---

*Status verified against the repository on 18 Aug 2026. All 101 backend tests pass; the app builds and lints clean in CI.*