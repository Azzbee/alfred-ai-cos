# Albert

Mobile-first AI chief of staff. Albert connects to Gmail and Calendar, finds what
you are forgetting, ranks what matters today, and prepares drafts you approve before
anything is sent.

This repo is the foundation for the first vertical slice:

```
Gmail OAuth → email ingestion → commitment extraction → Today priorities → draft reply
```

Nothing beyond that slice is built. No payments, browser automation, WhatsApp, or
delivery integrations. See [TODO.md](./TODO.md) for what comes next and
[ARCHITECTURE.md](./ARCHITECTURE.md) for why it is shaped this way.

## Layout

```
backend/              FastAPI app, Postgres models, AI pipeline, Celery workers
  app/api/v1/         HTTP routes (auth, sync, today, commitments, drafts, actions)
  app/db/             SQLAlchemy models + enums
  app/llm/            Provider-agnostic LLM interface; Anthropic impl isolated in providers/
  app/services/       OAuth, Gmail, ingestion, extraction, priority engine, Today builder
  app/workers/        Celery app + tasks
  migrations/         Alembic
mobile/               React Native / Expo app (Expo Router)
  app/                Routes (index = Today / Connect)
  src/                api client, screens, components, theme
packages/shared-types/  TypeScript types mirrored from backend schemas
docs/                 (reserved for deeper design notes)
```

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- [bun](https://bun.sh)
- Docker (for local Postgres + Redis)
- A Google Cloud OAuth client (Gmail + Calendar scopes)
- An Anthropic API key

## Setup

```bash
# 1. Infra
docker compose up -d

# 2. Secrets
cp .env.example .env       # fill in Google + Anthropic credentials
cp .env backend/.env       # backend reads its own .env

# 3. Backend
cd backend
uv sync
uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# 4. Worker (separate shell, for background sync)
uv run celery -A app.workers.celery_app worker --loglevel=info

# 5. Mobile (separate shell)
cd mobile
bun install
bun run start
```

The mobile app's API base URL is set in `mobile/app.json` under `extra.apiBaseUrl`.
For a device or simulator, point it at your machine's LAN IP, not `localhost`.

## The slice, end to end

1. **Connect.** The app calls `GET /api/v1/auth/google/start`, opens Google consent,
   and the backend redirects to `albert://auth?token=...` with an Albert session JWT.
2. **Sync.** `POST /api/v1/sync` ingests recent Gmail messages, classifies each, and
   extracts commitments with evidence and confidence.
3. **Today.** `GET /api/v1/today` ranks open commitments with a transparent, explainable
   priority engine and returns the dashboard.
4. **Draft.** `POST /api/v1/drafts` generates a reply (no approval needed; it is internal
   preparation).
5. **Approve.** `POST /api/v1/actions/propose-draft-to-gmail/{id}` then
   `POST /api/v1/actions/{id}/approve` pushes the draft into Gmail. Albert never sends.

## Verification

```bash
cd backend && uv run ruff check app tests && uv run mypy app && uv run pytest
cd ../packages/shared-types && bunx tsc --noEmit
cd ../../mobile && bunx tsc --noEmit
```

For local development without Google, mint a session in development mode:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/dev-session?email=you@example.com"
```
