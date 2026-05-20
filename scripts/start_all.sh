#!/usr/bin/env bash
# start_all.sh — One-shot script to set up and run the full BioWeb stack.
#
# Usage:
#   ./scripts/start_all.sh
#
# Options:
#   --skip-deps    Skip dependency installation (pip / npm)
#   --backend-only Start only the backend
#   --frontend-only Start only the frontend

set -euo pipefail

SKIP_DEPS=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --skip-deps)    SKIP_DEPS=true ;;
    --backend-only) BACKEND_ONLY=true ;;
    --frontend-only) FRONTEND_ONLY=true ;;
    -h|--help)
      sed -n '2,15p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      exit 1
      ;;
  esac
done

# ---------- helpers ----------
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
NVM_NODE_DIR="$HOME/.nvm/versions/node/v24.15.0/bin"
FRONTEND_DIR="$ROOT_DIR/frontend"
PORT="${PORT:-8010}"

info()  { echo -e "\033[36m[info]\033[0m  $*"; }
ok()    { echo -e "\033[32m[ok]\033[0m    $*"; }
warn()  { echo -e "\033[33m[warn]\033[0m  $*"; }
error() { echo -e "\033[31m[error]\033[0m $*"; exit 1; }

# ---------- .env ----------
if [ ! -f "$ROOT_DIR/.env" ]; then
  if [ -f "$ROOT_DIR/.env.example" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    info "Created .env from .env.example"
  else
    warn "No .env or .env.example found — backend may fail without required env vars."
  fi
fi

# ---------- node ----------
export PATH="$NVM_NODE_DIR:$PATH"
if ! command -v node &>/dev/null; then
  error "node not found. Install Node.js v24.15.0 via nvm, or update NVM_NODE_DIR in this script."
fi
ok "node $(node --version)"

# ---------- backend ----------
setup_backend() {
  info "Setting up backend…"

  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    info "Created Python virtualenv"
  fi
  source "$VENV_DIR/bin/activate"

  if ! $SKIP_DEPS; then
    pip install -r "$ROOT_DIR/requirements.txt" -q
    pip install -e "$ROOT_DIR/packages/bioweb_analysis" -q
    ok "Python dependencies installed"
  else
    info "Skipping pip dependency installation (--skip-deps)"
  fi

  ok "Backend ready"
}

# ---------- frontend ----------
setup_frontend() {
  info "Setting up frontend…"

  if ! $SKIP_DEPS; then
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
      (cd "$FRONTEND_DIR" && npm install --registry=https://registry.npmmirror.com)
      ok "npm dependencies installed"
    else
      info "node_modules already exists, skipping npm install"
    fi
  else
    info "Skipping npm dependency installation (--skip-deps)"
  fi

  ok "Frontend ready"
}

# ---------- start ----------
PIDS=()

start_backend() {
  setup_backend
  info "Starting backend on port $PORT …"
  (
    cd "$ROOT_DIR"
    source "$VENV_DIR/bin/activate"
    PORT=$PORT uvicorn backend.app.main:app --reload --host 0.0.0.0 --port "$PORT"
  ) &
  PIDS+=($!)
  ok "Backend PID ${PIDS[-1]}"
}

start_frontend() {
  setup_frontend
  info "Starting frontend (Vite dev server) …"
  (
    cd "$FRONTEND_DIR"
    npm run dev -- --host 0.0.0.0
  ) &
  PIDS+=($!)
  ok "Frontend PID ${PIDS[-1]}"
}

# ---------- cleanup ----------
cleanup() {
  echo ""
  info "Shutting down…"
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
    fi
  done
  wait 2>/dev/null
  ok "All processes stopped. Bye!"
}
trap cleanup EXIT INT TERM

# ---------- main ----------
if $BACKEND_ONLY; then
  start_backend
elif $FRONTEND_ONLY; then
  start_frontend
else
  setup_backend
  setup_frontend
  start_backend
  start_frontend
fi

echo ""
echo "============================================"
echo "  BioWeb is running!"
  if ! $FRONTEND_ONLY; then
    echo "  Backend:  http://localhost:$PORT"
    echo "  API docs: http://localhost:$PORT/docs"
  fi
  if ! $BACKEND_ONLY; then
    echo "  Frontend: http://localhost:5173"
  fi
echo "============================================"
echo ""
echo "Press Ctrl+C to stop."

# Wait for all background processes
wait
