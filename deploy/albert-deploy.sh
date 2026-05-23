#!/usr/bin/env bash
# Albert deploy / redeploy on the Hetzner VPS. Idempotent: pull, build a git-sha-tagged
# image, bring the stack up, run migrations once the DB is healthy. Run from the repo
# root on the server. Requires /opt/albert/.env (or a .env beside the compose file).
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -p albert -f docker-compose.prod.yml"

# Tag images by git sha so a rollback is just ALBERT_TAG=<old-sha> ./albert-deploy.sh.
export ALBERT_TAG="$(git rev-parse --short HEAD)"
echo "→ deploying albert @ ${ALBERT_TAG}"

git pull --ff-only
$COMPOSE build
$COMPOSE up -d

# Wait for Postgres to report healthy before migrating.
echo "→ waiting for albert_postgres to be healthy…"
until [ "$(docker inspect -f '{{.State.Health.Status}}' albert_postgres 2>/dev/null)" = "healthy" ]; do
  sleep 2
done

echo "→ running migrations (alembic upgrade head)"
$COMPOSE exec -T albert_web alembic upgrade head

echo "✓ albert @ ${ALBERT_TAG} is live on 127.0.0.1:${ALBERT_WEB_PORT:-8011} (behind Caddy)"
$COMPOSE ps
