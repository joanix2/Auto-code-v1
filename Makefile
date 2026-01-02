.PHONY: help start stop restart logs build clean test

help:
	@echo "Auto-Code Platform - Available Commands"
	@echo "========================================"
	@echo "make start       - Start all services"
	@echo "make stop        - Stop all services"
	@echo "make restart     - Restart all services"
	@echo "make logs        - View logs from all services"
	@echo "make build       - Build all containers"
	@echo "make clean       - Remove containers and volumes"
	@echo "make test-backend - Run backend tests"
	@echo "make test-frontend - Run frontend tests"
	@echo "make shell-backend - Open backend shell"
	@echo "make shell-frontend - Open frontend shell"

start:
	@echo "Starting Auto-Code Platform..."
	docker-compose up -d
	@echo "Services started! Access at:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000/api"
	@echo "  RabbitMQ: http://localhost:15672"

stop:
	@echo "Stopping all services..."
	docker-compose down

restart: stop start

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker

logs-frontend:
	docker-compose logs -f frontend

build:
	@echo "Building all containers..."
	docker-compose build

clean:
	@echo "Removing all containers, networks, and volumes..."
	docker-compose down -v
	@echo "Cleanup complete!"

test-backend:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-rabbitmq:
	docker-compose exec rabbitmq /bin/bash

dev-backend:
	@echo "Starting backend in development mode..."
	@if [ -d "backend/venv" ]; then \
		echo "Using virtual environment..."; \
		cd backend && ./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "Virtual environment not found. Run 'make install-backend' first."; \
		cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000; \
	fi

dev-worker:
	@echo "Starting worker in development mode..."
	@if [ -d "backend/venv" ]; then \
		cd backend && ./venv/bin/python worker.py; \
	else \
		cd backend && python worker.py; \
	fi

dev-frontend:
	@echo "Starting frontend in development mode..."
	cd frontend && npm start

install-backend:
	@echo "Installing backend dependencies..."
	@if [ ! -d "backend/venv" ]; then \
		echo "Creating virtual environment..."; \
		cd backend && python3 -m venv venv; \
	fi
	@echo "Installing dependencies in virtual environment..."
	cd backend && ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt
	@echo "Backend dependencies installed in venv!"

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install: install-backend install-frontend
	@echo "All dependencies installed!"

status:
	@echo "Service Status:"
	@docker-compose ps
