#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Auto-Code E2E Test Runner ==="

# Parse args
STACK_MODE="existing"
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --docker) STACK_MODE="docker" ;;
    --dev) STACK_MODE="dev" ;;
    *) echo "Usage: $0 [--docker|--dev]"; exit 1 ;;
  esac
  shift
done

if [ "$STACK_MODE" = "docker" ]; then
  echo "Starting stack via docker compose..."
  cd "$PROJECT_DIR"
  docker compose -f docker-compose.e2e.yml up --build -d neo4j backend frontend

  echo "Waiting for services to be ready..."
  sleep 10

  # Wait for backend health
  for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
      echo "Backend ready on port 8000"
      break
    fi
    echo "Waiting for backend... ($i/30)"
    sleep 2
  done

  # Wait for frontend
  for i in $(seq 1 15); do
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
      echo "Frontend ready on port 3000"
      break
    fi
    echo "Waiting for frontend... ($i/15)"
    sleep 2
  done

elif [ "$STACK_MODE" = "dev" ]; then
  echo "Starting dev servers..."
  cd "$PROJECT_DIR/backend"
  echo "Starting backend (uvicorn)..."
  uvicorn main:app --host 0.0.0.0 --port 8000 &
  BACKEND_PID=$!

  cd "$PROJECT_DIR/frontend"
  echo "Starting frontend (vite)..."
  npm run dev &
  FRONTEND_PID=$!

  sleep 5

  # Wait for backend
  for i in $(seq 1 20); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
      echo "Backend ready"
      break
    fi
    sleep 2
  done

  # Wait for frontend
  for i in $(seq 1 10); do
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
      echo "Frontend ready"
      break
    fi
    sleep 2
  done
fi

# Run tests
echo ""
echo "Running Playwright e2e tests..."
cd "$PROJECT_DIR/frontend"
set +e
npx playwright test --reporter=list "$@"
EXIT_CODE=$?
set -e

# Cleanup
if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID" 2>/dev/null; fi
if [ -n "$FRONTEND_PID" ]; then kill "$FRONTEND_PID" 2>/dev/null; fi
if [ "$STACK_MODE" = "docker" ]; then
  echo "Stopping docker stack..."
  docker compose -f "$PROJECT_DIR/docker-compose.e2e.yml" down
fi

echo ""
echo "=== Exit code: $EXIT_CODE ==="
exit $EXIT_CODE
