#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/service-api/service-python"
WEB_DIR="$ROOT_DIR/client-web"
COMPOSE_FILE="$ROOT_DIR/infra/docker-compose.yml"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-moodapi}"

log() { printf "\033[0;37m[build] %s\033[0m\n" "$1"; }
ok() { printf "\033[0;32m[ok] %s\033[0m\n" "$1"; }
warn() { printf "\033[1;33m[warn] %s\033[0m\n" "$1"; }
fail() { printf "\033[0;31m[erro] %s\033[0m\n" "$1" >&2; exit 1; }

ensure_env() {
  if [ ! -f "$ROOT_DIR/.env" ]; then
    warn "Criando .env local com defaults seguros para desenvolvimento"
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  fi
}

compose() {
  docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" "$@"
}

ensure_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "Docker CLI nao encontrado no PATH"
  fi

  if ! docker version >/dev/null 2>&1; then
    fail "Docker Engine indisponivel. Reinicie o Docker Desktop e rode novamente: ./scripts/build.sh up"
  fi
}

quality() {
  log "Rodando qualidade Python"
  cd "$API_DIR"
  python -m ruff check app tests
  python -m mypy app

  log "Rodando qualidade frontend"
  cd "$WEB_DIR"
  npm install
  npm run lint
  npm run build
}

migrate() {
  log "Rodando migrations"
  cd "$API_DIR"
  python -m alembic upgrade head
}

smoke() {
  log "Executando smoke local da API"
  cd "$API_DIR"
  python - <<'PY'
from app.config import get_settings
settings = get_settings()
print(f"MoodAPI settings loaded: {settings.environment}")
PY
}

up() {
  ensure_env
  ensure_docker
  log "Subindo runtime Docker"
  compose up -d --build --remove-orphans
  ok "API: http://localhost:8000"
  ok "Frontend: http://localhost:3000"
  ok "Prometheus: http://localhost:9090"
  ok "Grafana: http://localhost:3001"
}

down() {
  ensure_docker
  log "Parando runtime Docker"
  compose down --remove-orphans
}

clean_docker() {
  ensure_docker
  log "Limpando containers antigos do MoodAPI"
  compose down --remove-orphans --volumes || true
  docker compose -p infra -f "$COMPOSE_FILE" down --remove-orphans --volumes || true
  docker image rm moodapi-api:local moodapi-frontend:local infra-api infra-frontend 2>/dev/null || true
  ok "Limpeza Docker concluida"
}

case "${1:-up}" in
  quality)
    quality
    ;;
  migrate)
    migrate
    ;;
  smoke)
    smoke
    ;;
  check)
    quality
    migrate
    smoke
    ;;
  up)
    up
    ;;
  down)
    down
    ;;
  clean)
    clean_docker
    ;;
  restart)
    down
    up
    ;;
  ps)
    ensure_docker
    compose ps
    ;;
  logs)
    ensure_docker
    compose logs -f "${2:-api}"
    ;;
  *)
    echo "Uso: ./scripts/build.sh [up|down|clean|restart|ps|logs|quality|migrate|smoke|check]"
    exit 1
    ;;
esac
