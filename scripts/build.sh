#!/bin/bash

# ============================================
# MoodAPI - One-Click Build & Start
# ============================================
# Uso:
#   ./scripts/build.sh          # Docker mode (API + Frontend)
#   ./scripts/build.sh --local  # Local mode (sem Docker)
# ============================================

set -e

# Colors
log() { echo -e "\033[0;37m[LOG] $1\033[0m"; }
success() { echo -e "\033[0;32m[SUCESSO] $1\033[0m"; }
error() { echo -e "\033[0;31m[ERRO] $1\033[0m"; }
warning() { echo -e "\033[1;33m[AVISO] $1\033[0m"; }

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/dockerfile/docker-compose.yml"

cd "$PROJECT_ROOT"

echo ""
echo "============================================"
echo "  MOODAPI - Build & Start"
echo "============================================"
echo ""

# Check/Create .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    warning ".env file not found. Creating from defaults..."
    cat > "$PROJECT_ROOT/.env" << 'EOF'
MOODAPI_DEBUG=true
MOODAPI_ENVIRONMENT=development
MOODAPI_LOG_LEVEL=INFO
MOODAPI_DATABASE__URL=sqlite:///./data/sentiments.db
MOODAPI_CACHE__URL=redis://localhost:6379/0
MOODAPI_RATE_LIMIT__ENABLED=false
MOODAPI_JWT_SECRET_KEY=your-super-secret-key-change-in-production
EOF
else
    success ".env encontrado"
fi

# Create data directory
mkdir -p "$PROJECT_ROOT/data"

# Check for --local flag
if [ "$1" == "--local" ]; then
    log "Modo LOCAL selecionado"
    
    # Kill existing processes
    npx kill-port 5173 8000 2>/dev/null || true
    
    # Backend setup
    log "Configurando Python backend..."
    
    if [ ! -d ".venv" ]; then
        python -m venv .venv
    fi
    
    source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
    pip install -r requirements.txt --quiet
    
    # Start backend
    log "Iniciando backend em http://localhost:8000 ..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    sleep 3
    
    # Frontend setup
    log "Configurando React frontend..."
    cd "$PROJECT_ROOT/frontend"
    npm install --silent 2>/dev/null || npm install
    
    log "Iniciando frontend em http://localhost:5173 ..."
    npm run dev &
    FRONTEND_PID=$!
    sleep 3
    
    cd "$PROJECT_ROOT"
    
    echo ""
    echo "============================================"
    echo "  MOODAPI RUNNING (Local)"
    echo "============================================"
    echo "  API:       http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "--------------------------------------------"
    echo "  FRONTEND:  http://localhost:5173"
    echo "--------------------------------------------"
    warning "Pressione Ctrl+C para parar"
    echo "============================================"
    echo ""
    
    cleanup() {
        echo ""
        log "Parando serviços..."
        kill $FRONTEND_PID 2>/dev/null || true
        kill $BACKEND_PID 2>/dev/null || true
        success "Serviços parados."
        exit 0
    }
    
    trap cleanup SIGINT SIGTERM
    wait
    exit 0
fi

# Docker mode
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    error "docker-compose.yml não encontrado em $DOCKER_COMPOSE_FILE"
    exit 1
fi

log "Limpando ambiente Docker antigo..."
docker compose -f "$DOCKER_COMPOSE_FILE" down --volumes --remove-orphans

log "Removendo volumes antigos..."
docker volume prune -f

log "Limpando imagens antigas do projeto..."
docker rmi -f moodapi-api moodapi-frontend dockerfile-api dockerfile-frontend 2>/dev/null || true

log "Construindo novas imagens Docker do zero..."
docker compose -f "$DOCKER_COMPOSE_FILE" build --no-cache

success "Imagens construídas com sucesso."

log "Iniciando todos os serviços..."
docker compose -f "$DOCKER_COMPOSE_FILE" up -d

# Wait for startup
sleep 5

echo ""
echo "============================================"
echo "  MOODAPI RUNNING (Docker)"
echo "============================================"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/health"
echo "--------------------------------------------"
echo "  FRONTEND:  http://localhost:3000"
echo "--------------------------------------------"
echo "  Logs:  docker compose -f dockerfile/docker-compose.yml logs -f"
echo "  Stop:  docker compose -f dockerfile/docker-compose.yml down"
echo "============================================"
echo ""
