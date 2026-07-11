# Example docker Deployment file 
set -euo pipefail

APP_DIR="/opt/harvee-assessment"
COMPOSE_FILE="docker-compose.prod.yml"
BRANCH="${DEPLOY_BRANCH:-main}"

log() { echo "[deploy] $(date '+%Y-%m-%d %H:%M:%S') $*"; }

cd "$APP_DIR"

log "Fetching latest code (branch: $BRANCH)..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

if [ ! -f ".env.prod" ]; then
  log "ERROR: .env.prod not found in $APP_DIR. Copy .env.prod.example, fill in production secrets, save as .env.prod, then re-run."
  exit 1
fi

log "Building images for both tasks..."
docker compose -f "$COMPOSE_FILE" build --pull

log "Restarting stack via systemd (picks up new images)..."
sudo systemctl restart harvee-assessment.service

log "Waiting for Task 1 backend health check (via frontend proxy on :8080)..."
for i in $(seq 1 20); do
  if curl -fs http://127.0.0.1:8080/api/health > /dev/null 2>&1; then
    log "Task 1 backend healthy."
    break
  fi
  if [ "$i" -eq 20 ]; then
    log "ERROR: Task 1 backend did not become healthy within 60s. Check: docker compose -f $COMPOSE_FILE logs task1-backend"
    exit 1
  fi
  sleep 3
done

log "Waiting for Task 2 backend health check (via frontend proxy on :8081)..."
for i in $(seq 1 20); do
  if curl -fs http://127.0.0.1:8081/api/health > /dev/null 2>&1; then
    log "Task 2 backend healthy."
    break
  fi
  if [ "$i" -eq 20 ]; then
    log "ERROR: Task 2 backend did not become healthy within 60s. Check: docker compose -f $COMPOSE_FILE logs task2-backend"
    exit 1
  fi
  sleep 3
done

log "Running production readonly-role provisioning for Task 2 (idempotent)..."
docker compose -f "$COMPOSE_FILE" exec -T task2-db psql -U "${TASK2_POSTGRES_USER}" -d "${TASK2_POSTGRES_DB}" \
  -v readonly_password="'${TASK2_READONLY_DB_PASSWORD}'" \
  -f /dev/stdin < task2-ai-sql-assistant/deploy/provision-readonly-role.sql || \
  log "WARNING: readonly role provisioning script failed or role already correctly configured — check manually if this is unexpected."

log "Pruning old, dangling images..."
docker image prune -f > /dev/null

log "Deployment complete."
