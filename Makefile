# ============================================================================
# Customer Success FTE — Makefile
# ============================================================================
# Common commands for development, testing, and deployment.
#
# Usage:
#   make dev          Start the full local stack (docker-compose)
#   make stop         Stop the local stack
#   make build        Build the Docker image
#   make test         Run all tests
#   make test-unit    Run unit tests only (no live services needed)
#   make test-e2e     Run end-to-end tests (requires docker-compose)
#   make lint         Run ruff linter
#   make migrate      Apply database schema to running PostgreSQL
#   make deploy       Deploy to Kubernetes (kubectl apply)
#   make logs         Tail logs from all running containers
#   make clean        Remove all build artifacts and __pycache__
# ============================================================================

.PHONY: all dev stop build test test-unit test-e2e lint migrate \
        deploy deploy-k8s logs clean web-dev web-build help

# ─── Variables ──────────────────────────────────────────────────────────────

IMAGE_NAME    := customer-success-fte
IMAGE_TAG     := latest
REGISTRY      := ghcr.io/your-org
K8S_NAMESPACE := fte
COMPOSE_FILE  := docker-compose.yml
PYTHON        := python
PIP           := pip
PYTEST        := python -m pytest
PROJECT_DIR   := $(shell pwd)

# ─── Default target ─────────────────────────────────────────────────────────

all: help

# ─── Development ────────────────────────────────────────────────────────────

dev:
	@echo "Starting full local development stack..."
	docker compose -f $(COMPOSE_FILE) up -d
	@echo ""
	@echo "Services started:"
	@echo "  API:       http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Web Form:  http://localhost:3000"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Kafka:     localhost:9092"
	@echo ""
	@echo "Run 'make logs' to tail all container logs"

stop:
	@echo "Stopping all services..."
	docker compose -f $(COMPOSE_FILE) down

restart:
	@echo "Restarting all services..."
	docker compose -f $(COMPOSE_FILE) restart

logs:
	docker compose -f $(COMPOSE_FILE) logs -f --tail=100

logs-api:
	docker compose -f $(COMPOSE_FILE) logs -f --tail=100 fte-api

logs-worker:
	docker compose -f $(COMPOSE_FILE) logs -f --tail=100 fte-worker

# ─── Build ──────────────────────────────────────────────────────────────────

build:
	@echo "Building Docker image $(IMAGE_NAME):$(IMAGE_TAG)..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "Build complete: $(IMAGE_NAME):$(IMAGE_TAG)"

build-push:
	@echo "Building and pushing to registry..."
	docker build -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) .
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

# ─── Testing ────────────────────────────────────────────────────────────────

test:
	@echo "Running all tests..."
	$(PYTEST) tests/ -v --tb=short

test-unit:
	@echo "Running unit tests (no live services required)..."
	$(PYTEST) tests/test_agent.py tests/test_channels.py tests/test_transition.py \
	    -v --tb=short

test-e2e:
	@echo "Running end-to-end tests (requires running services)..."
	$(PYTEST) tests/test_e2e.py -v --tb=short

test-load:
	@echo "Running Locust load test (30s smoke)..."
	locust -f tests/load_test.py --headless \
	    --users 5 --spawn-rate 1 --run-time 30s \
	    --host http://localhost:8000

test-cov:
	@echo "Running tests with coverage report..."
	$(PYTEST) tests/ -v --tb=short \
	    --cov=production --cov-report=term-missing --cov-report=html:htmlcov

# ─── Code Quality ───────────────────────────────────────────────────────────

lint:
	@echo "Running ruff linter..."
	ruff check production/ incubation/ tests/ --fix

format:
	@echo "Running ruff formatter..."
	ruff format production/ incubation/ tests/

typecheck:
	@echo "Running mypy type checker..."
	mypy production/ --ignore-missing-imports

# ─── Database ───────────────────────────────────────────────────────────────

migrate:
	@echo "Applying database schema..."
	docker compose exec postgres psql -U fte_user -d fte_db \
	    -f /docker-entrypoint-initdb.d/schema.sql
	@echo "Schema applied successfully"

migrate-fresh:
	@echo "WARNING: Dropping and recreating the database..."
	docker compose exec postgres psql -U fte_user -c "DROP DATABASE IF EXISTS fte_db;"
	docker compose exec postgres psql -U fte_user -c "CREATE DATABASE fte_db;"
	$(MAKE) migrate

db-shell:
	@echo "Opening PostgreSQL shell..."
	docker compose exec postgres psql -U fte_user -d fte_db

db-backup:
	@echo "Creating database backup..."
	docker compose exec postgres pg_dump -U fte_user fte_db \
	    > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved"

# ─── Dependencies ───────────────────────────────────────────────────────────

install:
	@echo "Installing Python dependencies..."
	$(PIP) install -r production/requirements.txt

install-dev:
	@echo "Installing development dependencies..."
	$(PIP) install -r production/requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov ruff mypy locust

# ─── Web Form ───────────────────────────────────────────────────────────────

web-dev:
	@echo "Starting Next.js web form in development mode..."
	cd web-form && npm run dev

web-build:
	@echo "Building Next.js web form for production..."
	cd web-form && npm run build

web-install:
	@echo "Installing Next.js dependencies..."
	cd web-form && npm install

# ─── Kubernetes Deployment ──────────────────────────────────────────────────

deploy: deploy-k8s

deploy-k8s:
	@echo "Deploying to Kubernetes namespace: $(K8S_NAMESPACE)..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/deployment-api.yaml
	kubectl apply -f k8s/deployment-worker.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml
	kubectl apply -f k8s/hpa.yaml
	@echo "Deployment complete"
	@echo ""
	kubectl get pods -n $(K8S_NAMESPACE)

k8s-status:
	@echo "Kubernetes deployment status:"
	kubectl get pods,services,hpa -n $(K8S_NAMESPACE)

k8s-logs:
	kubectl logs -n $(K8S_NAMESPACE) -l app=fte-api -f --tail=100

k8s-rollout:
	@echo "Rolling restart of all pods..."
	kubectl rollout restart deployment/fte-api -n $(K8S_NAMESPACE)
	kubectl rollout restart deployment/fte-worker -n $(K8S_NAMESPACE)

k8s-delete:
	@echo "WARNING: Deleting all FTE resources from Kubernetes..."
	kubectl delete namespace $(K8S_NAMESPACE)

# ─── Health Checks ──────────────────────────────────────────────────────────

health:
	@echo "Checking API health..."
	curl -s http://localhost:8000/health | python -m json.tool

health-ready:
	@echo "Checking API readiness..."
	curl -s http://localhost:8000/health/ready | python -m json.tool

metrics:
	@echo "Fetching channel metrics..."
	curl -s http://localhost:8000/metrics/channels | python -m json.tool

# ─── Cleanup ────────────────────────────────────────────────────────────────

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "Clean complete"

clean-docker:
	@echo "Removing Docker containers, images, and volumes..."
	docker compose -f $(COMPOSE_FILE) down -v --rmi local
	@echo "Docker clean complete"

# ─── Help ───────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Customer Success FTE — Available Commands"
	@echo "========================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev          Start full local stack (docker-compose up -d)"
	@echo "  make stop         Stop all services"
	@echo "  make restart      Restart all services"
	@echo "  make logs         Tail all container logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-unit    Run unit tests only (no live services)"
	@echo "  make test-e2e     Run end-to-end tests"
	@echo "  make test-load    Run 30s Locust smoke test"
	@echo "  make test-cov     Run tests with HTML coverage report"
	@echo ""
	@echo "Build:"
	@echo "  make build        Build Docker image"
	@echo "  make build-push   Build and push to registry"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      Apply schema.sql to running PostgreSQL"
	@echo "  make db-shell     Open psql shell"
	@echo "  make db-backup    Create a database backup"
	@echo ""
	@echo "Web Form:"
	@echo "  make web-dev      Start Next.js dev server"
	@echo "  make web-build    Build Next.js for production"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make deploy       Deploy all K8s manifests"
	@echo "  make k8s-status   Show pod/service/HPA status"
	@echo "  make k8s-rollout  Rolling restart all pods"
	@echo ""
	@echo "Utilities:"
	@echo "  make health       Check /health endpoint"
	@echo "  make metrics      Check /metrics/channels endpoint"
	@echo "  make lint         Run ruff linter"
	@echo "  make clean        Remove __pycache__ and build artifacts"
	@echo ""
