# Conversational Business OS (CBO)

A production-ready side project for managing retail businesses through conversation.

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.13+
- Docker Desktop (for PostgreSQL and Redis)

### Setup

1. Install frontend dependencies:

```bash
npm install
```

2. Install backend dependencies:

```bash
pip install -r apps/api/requirements.txt
```

3. Start services:

```bash
docker compose up -d
```

4. Copy environment files:

```bash
cp .env.example apps/api/.env
cp apps/web/.env.local.example apps/web/.env.local
```

5. Start development servers:

```bash
# Frontend (http://localhost:3000)
npm run start:dev --filter=web

# Backend (http://localhost:8000)
uvicorn app.main:app --reload --app-dir apps/api
```

### Project Structure

```
apps/
  api/      - FastAPI backend
  web/      - Next.js frontend
packages/
  shared/   - Shared TypeScript types
  config/   - Shared configuration
```

### Verification

- Backend health: `GET http://localhost:8000/health`
- Frontend: `http://localhost:3000`
