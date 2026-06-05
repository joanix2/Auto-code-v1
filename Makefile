.PHONY: help start stop restart logs build clean test deploy-local deploy-aws kill

help:
	@echo "╔═══════════════════════════════════════════════╗"
	@echo "║  AutoCode Platform - Available Commands       ║"
	@echo "╚═══════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make dev-backend      - Start backend in development mode"
	@echo "  make dev-frontend     - Start frontend in development mode"
	@echo "  make dev-worker       - Start worker in development mode"
	@echo ""
	@echo "🐳 Docker Operations:"
	@echo "  make start-dev        - Start development services (no NPM)"
	@echo "  make start            - Start production services (with NPM)"
	@echo "  make stop             - Stop all Docker services"
	@echo "  make restart          - Restart development services"
	@echo "  make restart-prod     - Restart production services"
	@echo "  make build            - Build production containers"
	@echo "  make build-dev        - Build development containers"
	@echo "  make logs             - View logs from all services"
	@echo "  make clean            - Remove containers and volumes"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install-backend  - Install backend dependencies in venv"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make install-all      - Install all dependencies"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test-backend     - Run backend tests"
	@echo "  make test-frontend    - Run frontend tests"
	@echo "  make deploy-local     - Test deployment locally"
	@echo ""
	@echo "☁️  AWS Deployment:"
	@echo "  make deploy-aws       - Deploy infrastructure to AWS"
	@echo "  make tf-init          - Initialize Terraform"
	@echo "  make tf-plan          - Plan Terraform changes"
	@echo "  make tf-apply         - Apply Terraform changes"
	@echo "  make tf-destroy       - Destroy AWS infrastructure"
	@echo ""
	@echo "🔧 Utilities:"
	@echo "  make shell-backend    - Open backend shell"
	@echo "  make shell-backend    - Open backend shell"
	@echo "  make shell-frontend   - Open frontend shell"
	@echo "  make shell-neo4j      - Open Neo4j shell"
	@echo ""
	@echo "🔧 Kill:"
	@echo "  make kill              - Kill backend and frontend instances"

# Development mode (without NPM)
start-dev:
	@echo "🔧 Starting AutoCode Platform (Development Mode)..."
	docker compose -f docker-compose.dev.yml up -d
	@echo "✅ Development services started!"
	@echo ""
	@echo "Access your services at:"
	@echo "  Frontend:   http://localhost:3000"
	@echo "  Backend:    http://localhost:8000/docs"
	@echo "  Neo4j:      http://localhost:7474"

# Production mode (with NPM)
start:
	@echo "🚀 Starting AutoCode Platform (Production Mode)..."
	docker compose up -d
	@echo "✅ Production services started!"
	@echo ""
	@echo "Access your services at:"
	@echo "  Frontend:   http://localhost:3000"
	@echo "  Backend:    http://localhost:8000/docs"
	@echo "  Neo4j:      http://localhost:7474"
	@echo "  NPM Admin:  http://localhost:81"

stop:
	@echo "🛑 Stopping all services..."
	docker compose down
	docker compose -f docker-compose.dev.yml down

restart: stop start-dev

restart-prod: stop start

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

logs-neo4j:
	docker compose logs -f neo4j

logs-npm:
	docker compose logs -f nginx-proxy-manager

build:
	@echo "🔨 Building all containers (production)..."
	docker compose build

build-dev:
	@echo "🔨 Building all containers (development)..."
	docker compose -f docker-compose.dev.yml build

clean:
	@echo "🗑️  Removing all containers, networks, and volumes..."
	docker compose down -v
	docker compose -f docker-compose.dev.yml down -v
	@echo "✅ Cleanup complete!"

# Installation
install-backend:
	@echo "📦 Installing backend dependencies..."
	@if [ ! -d "backend/venv" ]; then \
		echo "Creating virtual environment..."; \
		cd backend && python3 -m venv venv; \
	fi
	@echo "Installing dependencies in virtual environment..."
	cd backend && ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt
	@echo "✅ Backend dependencies installed!"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed!"

install-all: install-backend install-frontend
	@echo "✅ All dependencies installed!"

# Linting
lint-backend:
	@echo "🔍 Linting backend..."
	cd backend && ./venv/bin/ruff check .
	cd backend && ./venv/bin/ruff format --check .

lint-backend-fix:
	@echo "🔧 Fixing backend lint..."
	cd backend && ./venv/bin/ruff check --fix .
	cd backend && ./venv/bin/ruff format .

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint
	cd frontend && npm run format

lint-frontend-fix:
	@echo "🔧 Fixing frontend lint..."
	cd frontend && npm run lint:fix
	cd frontend && npm run format:fix

lint-all: lint-backend lint-frontend
	@echo "✅ All linters passed!"

typecheck-backend:
	@echo "🔍 Type checking backend..."
	cd backend && ./venv/bin/mypy src/ --ignore-missing-imports

typecheck-frontend:
	@echo "🔍 Type checking frontend..."
	cd frontend && npm run typecheck

typecheck-all: typecheck-backend typecheck-frontend
	@echo "✅ All type checks passed!"

check-all: lint-all typecheck-all test-backend test-frontend
	@echo "✅ All checks passed!"

# Testing
test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && python -m pytest tests/ -v

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test

deploy-local:
	@echo "🧪 Testing deployment locally..."
	@bash test-deployment.sh

# Development mode
dev-backend:
	@echo "🔧 Starting backend in development mode..."
	@if [ -d "backend/venv" ]; then \
		echo "Using virtual environment..."; \
		cd backend && ./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "⚠️  Virtual environment not found. Run 'make install-backend' first."; \
		cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000; \
	fi

dev-frontend:
	@echo "🔧 Starting frontend in development mode..."
	cd frontend && npm run dev

# AWS/Terraform commands
tf-init:
	@echo "🔧 Initializing Terraform..."
	cd IaC && terraform init

tf-plan:
	@echo "📋 Planning Terraform changes..."
	cd IaC && terraform plan

tf-apply:
	@echo "🚀 Applying Terraform changes..."
	cd IaC && terraform apply

tf-destroy:
	@echo "💥 Destroying AWS infrastructure..."
	@echo "⚠️  WARNING: This will delete all resources!"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || exit 1
	cd IaC && terraform destroy

deploy-aws:
	@echo "🚀 Deploying to AWS..."
	cd IaC && bash bash/provision.sh

# Database operations
db-shell:
	@echo "Opening Neo4j Cypher Shell..."
	docker compose exec neo4j cypher-shell -u neo4j -p password

db-backup:
	@echo "📦 Creating Neo4j backup..."
	docker compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups
	@echo "✅ Backup created in Neo4j container at /backups/"

db-restore:
	@echo "⚠️  This will restore the database from backup"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker compose stop neo4j
	docker compose exec neo4j neo4j-admin database load neo4j --from-path=/backups
	docker compose start neo4j
	@echo "✅ Database restored!"

# Monitoring
status:
	@echo "📊 Service Status:"
	@docker compose ps
	@echo ""
	@echo "💾 Disk Usage:"
	@docker system df

health:
	@echo "🏥 Health Checks:"
	@echo -n "  Backend:  "
	@curl -f -s -o /dev/null http://localhost:8000 && echo "✅" || echo "❌"
	@echo -n "  Frontend: "
	@curl -f -s -o /dev/null http://localhost:3000 && echo "✅" || echo "❌"
	@echo -n "  Neo4j:    "
	@curl -f -s -o /dev/null http://localhost:7474 && echo "✅" || echo "❌"
	@echo -n "  NPM:      "
	@curl -f -s -o /dev/null http://localhost:81 && echo "✅" || echo "❌"

# Cleanup
prune:
	@echo "🧹 Cleaning up Docker system..."
	docker system prune -a --volumes -f
	@echo "✅ Cleanup complete!"
deploy-local:
	@echo "🧪 Testing deployment locally..."
	@bash test-deployment.sh

# Shell access
shell-backend:
	docker compose exec backend /bin/bash

shell-frontend:
	docker compose exec frontend /bin/sh

shell-neo4j:
	docker compose exec neo4j /bin/bash

shell-npm:
	docker compose exec nginx-proxy-manager /bin/sh

kill:
	@echo "🔪 Killing backend and frontend instances..."
	@-lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null; echo "  Backend (port 8000): killed"
	@-lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null; echo "  Frontend (port 3000): killed"
	@echo "✅ Done"

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install: install-backend install-frontend
	@echo "All dependencies installed!"

status:
	@echo "Service Status:"
	@docker-compose ps
