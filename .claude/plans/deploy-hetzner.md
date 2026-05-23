# Deploy plan: Albert backend → Hetzner VPS + app → EAS Update

Goal: friends in the US can test anytime, with their own Gmail, without Adam's laptop
running. Backend on Hetzner behind HTTPS; app published via EAS Update so Expo Go loads
it from Expo's cloud, not Metro on the Mac.

Legend: **[A]** = Adam does (needs your accounts/access) · **[C]** = Claude does (code/config).

---

## Decisions locked (from Adam)

- **Domain**: `albert.alfredassistants.com` (Adam owns alfredassistants.com). A record →
  Hetzner IP. NOT DuckDNS.
- **Shared VPS**: the box already runs **Alfred + Paperclip** behind an **existing Caddy**,
  with per-user Docker instances. Albert must coexist — no second Caddy, no port stomps.
- **Isolation strategy (recommended, pending Adam override)**:
  - Dedicated **Postgres + Redis for Albert** (own containers/volume/network) — Albert
    stores encrypted Gmail/Calendar tokens; do not mix into Alfred's DB (blast radius +
    migration collisions).
  - **Share the existing Caddy**: add a site block for albert.alfredassistants.com →
    reverse-proxy to Albert's web container. (Container Caddy → join its network; systemd
    Caddy → proxy to localhost:<albert-port>.)
  - **Own compose project** (`albert_*` names) so Albert's lifecycle never touches Alfred.
- **Production hardening (Adam treats this as prod, so decide now even if light for 3 testers)**:
  - Postgres volume: named volume + **nightly `pg_dump`** to a second path. Document it.
  - Images tagged (`albert-backend:<git-sha>`), **never `:latest`**, so rollback = redeploy a tag.
  - Logs: `docker compose logs` + json-file driver with rotation (max-size/max-file), not just tail-on-verify.

## VPS facts to gather first (Adam runs, read-only — output shapes the compose)

```
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
docker network ls
sudo ss -tlnp | grep -E ':(80|443|5432|6379|8000) '
which caddy; systemctl is-active caddy
ls /etc/caddy/ ; ls /opt
docker volume ls | grep -iE 'pg|postgres|redis'
```

Answers: Caddy container-vs-systemd, free ports for Albert's web container, whether a
shareable Postgres exists, where apps live on disk.

## Current state (verified)

- Backend: FastAPI, Python 3.12, `uv`, ~30 deps. Runs 3 processes: **uvicorn** (web),
  **celery worker**, **celery beat**. Reads config from `.env` (pydantic-settings).
- `docker-compose.yml` only runs local Postgres(pgvector) + Redis — no app service, no Dockerfile.
- App: Expo SDK 54, expo-router. No EAS configured, not logged into Expo.
- OAuth: works, but needs a STABLE https callback URL (ngrok churns). A real domain fixes this.

---

## Phase 1 — Containerize the backend [C]

1. Write `backend/Dockerfile` (python:3.12-slim, install uv, copy app, `uv sync`).
2. Write `docker-compose.prod.yml`: services = `web` (uvicorn), `worker` (celery),
   `beat` (celery beat), `postgres` (pgvector), `redis`. All on one network; web behind
   the reverse proxy. Named volume for Postgres.
3. Add `Caddyfile` (Caddy reverse proxy → automatic HTTPS via Let's Encrypt for the domain).
4. Verify locally: `docker compose -f docker-compose.prod.yml up` boots all 3 app processes.

## Phase 2 — Domain + DNS [A]

5. Pick a domain/subdomain pointing at the VPS, e.g. `api.<yourdomain>` or use a free
   option. **[A]** Create an A record → Hetzner VPS public IP. (Tell me the hostname.)
   - If you have no domain: a Hetzner-IP + Caddy self-cert won't satisfy Google OAuth.
     We need a real DNS name for HTTPS. Cheapest path: a $1-2/yr domain or a free
     subdomain (e.g. DuckDNS) — I'll flag options.

## Phase 3 — Provision the VPS [A] with my exact commands

6. **[A]** Give me SSH access (add my key, or you run the commands I write). Confirm the
   box has Docker + Docker Compose, or I provide the install steps.
7. **[A]** Copy secrets to the server: create `/opt/albert/.env` from your local `.env`
   but with PRODUCTION values — `ENVIRONMENT=production` (keeps dev endpoints off!),
   `APP_BASE_URL=https://<domain>`, `GOOGLE_OAUTH_REDIRECT_URI=https://<domain>/api/v1/auth/google/callback`,
   real `DATABASE_URL`/`REDIS_URL` pointing at the compose services, and a **≥32-byte
   `JWT_SECRET`** (current one is 29 bytes — regenerate; note this logs out existing sessions).
8. Pull the repo on the server, `docker compose -f docker-compose.prod.yml up -d`.
9. Run DB migrations on the server (alembic upgrade head).

## Phase 4 — Google OAuth for production [A]

10. **[A]** In Google Cloud Console → Credentials → OAuth client → Authorized redirect URIs,
    add `https://<domain>/api/v1/auth/google/callback`.
11. **[A]** OAuth consent screen → Test users: add all 3 friends' Gmail addresses.

## Phase 5 — Publish the app via EAS Update [A]+[C]

12. **[A]** Create a free Expo account; `npx expo login`.
13. **[C]** `bunx expo install expo-updates`; add `eas.json`, `runtimeVersion`, and the
    update config to `app.json`; set `extra.apiBaseUrl = https://<domain>` (the deployed backend).
14. **[C]** `eas init` (creates the project/projectId) — needs you logged in.
15. **[C]** `eas update --branch preview` to publish the JS bundle.
16. Friends open the **EAS Update link** in Expo Go (or scan its QR) — no Mac needed.
    - NOTE: the `albert://` vs `exp://` deep-link fix already shipped works for Expo Go;
      EAS Update keeps that behavior. Real native OAuth would want a dev/standalone build
      later, but Expo Go + the proxy redirect is fine for this testing round.

## Phase 6 — Verify [C]

17. Hit `https://<domain>/docs` (200), `/api/v1/me` (401) from a non-local network.
18. Walk one friend through: open EAS link → Connect Gmail → lands in app → data loads.
19. Tail server logs during the first real sign-in to confirm the chain.

---

## What I need from you to start (the blockers)

- **Domain**: a hostname for the VPS (or "I have none" → I'll give cheap/free options).
- **VPS access**: SSH (your key added for me) OR you run my commands; confirm Docker present.
- **Expo account**: created + `expo login` done (for Phase 5).
- **Secrets**: you place the production `.env` on the server (I never read your secrets).

## Cost / honesty notes

- Hetzner VPS: you already pay for it. Domain: ~$1-15/yr or free subdomain.
- Effort: ~half a day end to end, most of it one-time. After this, `eas update` +
  `git pull && docker compose up -d` is the whole redeploy loop.
- I cannot SSH to your VPS or log into Expo/Google for you — those steps are yours,
  with exact commands from me.
