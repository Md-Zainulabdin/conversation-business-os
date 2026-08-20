# CBO — Deployment Guide (Railway)

Deploy the backend (FastAPI) and frontend (Next.js) as two services in a single Railway project. Both are packaged as Docker images, so no runtime dependencies are needed beyond the services below.

---

## 1. Services to create

| Service | Root directory | Dockerfile | Config file |
|---------|----------------|------------|-------------|
| `api` (backend) | `apps/api` | `apps/api/Dockerfile` | `apps/api/railway.json` |
| `web` (frontend) | `.` (repo root) | `apps/web/Dockerfile` | `railway.json` |

The `web` service builds from the repo root because it is an npm workspace member and needs the root `package-lock.json`. The `api` service builds from `apps/api` directly.

### Create via dashboard
1. New project → Deploy from repo → select this repo.
2. Delete any auto-generated service. Add two services:
   - **API:** set Root Directory to `apps/api`. Railway picks up `apps/api/railway.json` automatically.
   - **Web:** set Root Directory to `.` (repo root). Railway picks up `railway.json` (dockerfile path `apps/web/Dockerfile`) automatically.

---

## 2. Backend environment variables (`api` service)

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Postgres connection string, e.g. `postgresql+asyncpg://user:pass@host/db` (Neon, Supabase, or Railway Postgres) |
| `REDIS_URL` | Redis connection string, e.g. `redis://default:pass@host:port` (Upstash Redis) |
| `SECRET_KEY` | Long random string for JWT signing. `openssl rand -hex 32` |
| `GROQ_API_KEY` | Groq key (used for both chat completions and Whisper transcription) |
| `ALLOWED_ORIGINS` | JSON array of allowed browser origins, e.g. `["https://web-production-xxxx.up.railway.app"]`. Include the web app's Railway URL (and `http://localhost:3000` during local dev) |
| `ENVIRONMENT` | `production` |
| `PORT` | Set by Railway automatically. The Dockerfile already binds to `$PORT` |

**Migrations:** `apps/api/railway.json` runs `alembic upgrade head` as a `preDeployCommand` before each deploy. It runs in the private network with the service env vars applied, so no extra work needed.

### Add a Postgres database
- Add a Railway Postgres plugin, then copy its `DATABASE_URL` into the `api` service env. Use the `postgresql` (non-pooler) URL so `asyncpg` connects directly.

---

## 3. Frontend environment (web service)

- `NEXT_PUBLIC_API_URL`: the public URL of the `api` service, e.g. `https://api-production-xxxx.up.railway.app`. **Must be set as a Build Variable** (build-time), because Next.js bakes it into the client bundle during the image build. Add it under the service → Variables → *Build Variables* section.

No runtime env vars are needed for the web container.

---

## 4. Health checks

- **API:** `apps/api/railway.json` sets `healthcheckPath: "/health"`. The app exposes `GET /health`.
- **Web:** `railway.json` sets `healthcheckPath: "/"`. The Next standalone server responds 200.

---

## 5. Verification

After both services show `Active` in Railway:

1. Open the API URL + `/health` → expect `{"status":"ok","version":"0.1.0"}`.
2. Open the web URL → register a fresh account → log in.
3. In the web app settings, set the store name/currency (persisted via `users.store_name` / `users.currency`).
4. Record a sale in the AI assistant (chat) and a normal sale form to confirm stock changes persist.
5. Confirm the low-stock bell in the header reflects `minimum_stock` thresholds.

---

## 6. CI/CD

`.github/workflows/ci.yml` runs quality checks on every PR/push to `main`, and on merge to `main` additionally deploys both services via the Railway CLI action. Required GitHub secrets:

| Secret | Value |
|--------|-------|
| `RAILWAY_TOKEN` | Railway API token (Account → Settings → Tokens) |
| `RAILWAY_API_SERVICE_ID` | ID of the `api` service (service → Settings → copy ID) |
| `RAILWAY_WEB_SERVICE_ID` | ID of the `web` service |

---

## 7. Local smoke test of the images (optional)

```bash
# backend
docker build -t cbo-api apps/api
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/cbo \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  cbo-api
# then curl http://localhost:8000/health

# frontend
docker build -t cbo-web -f apps/web/Dockerfile .
docker run --rm -p 3000:3000 cbo-web
# then open http://localhost:3000
```