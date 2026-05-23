#!/usr/bin/env bash
# Nightly Postgres backup for Albert. Dumps the DB from the running container to a gzip
# on a second path, keeps the last 7. Install on the VPS via cron:
#   0 3 * * * /opt/albert/repo/deploy/albert-backup.sh >> /var/log/albert-backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${ALBERT_BACKUP_DIR:-/opt/albert/backups}"
KEEP_DAYS="${ALBERT_BACKUP_KEEP:-7}"
DB_USER="${POSTGRES_USER:-albert}"
DB_NAME="${POSTGRES_DB:-albert}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/albert-${STAMP}.sql.gz"

echo "→ dumping ${DB_NAME} → ${OUT}"
docker exec albert_postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$OUT"

# Prune backups older than KEEP_DAYS.
find "$BACKUP_DIR" -name 'albert-*.sql.gz' -mtime "+${KEEP_DAYS}" -delete
echo "✓ backup done; keeping last ${KEEP_DAYS} days"
ls -lh "$BACKUP_DIR" | tail -5
