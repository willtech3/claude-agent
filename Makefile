# Claude Agent Makefile
# Standardized commands for development

# Variables
PYTHON := python3.12
UV := uv
FRONTEND_DIR := frontend
BACKEND_DIR := backend
AGENT_DIR := agent

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help
help: ## Show this help message
	@echo "$(CYAN)Claude Agent Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Backend Commands
.PHONY: backend-setup
backend-setup: ## Set up backend virtual environment and install dependencies
	@echo "$(YELLOW)Setting up backend environment...$(NC)"
	cd $(BACKEND_DIR) && $(UV) venv --python $(PYTHON)
	cd $(BACKEND_DIR) && $(UV) sync
	cd $(BACKEND_DIR) && $(UV) pip install -e ".[dev]"
	@echo "$(GREEN)Backend setup complete!$(NC)"

.PHONY: backend-test
backend-test: ## Run backend tests with pytest
	@echo "$(YELLOW)Running backend tests...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run pytest tests/ -v

.PHONY: backend-test-minimal
backend-test-minimal: ## Run minimal API tests
	@echo "$(YELLOW)Running minimal API tests...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run pytest tests/test_minimal_api.py tests/test_integration.py -v

.PHONY: backend-test-cov
backend-test-cov: ## Run backend tests with coverage
	@echo "$(YELLOW)Running backend tests with coverage...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run pytest tests/ -v --cov=app --cov-report=term-missing

.PHONY: backend-lint
backend-lint: ## Run ruff linter on backend code
	@echo "$(YELLOW)Linting backend code...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run ruff check app/ tests/

.PHONY: backend-format
backend-format: ## Format backend code with ruff
	@echo "$(YELLOW)Formatting backend code...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run ruff format app/ tests/

.PHONY: backend-typecheck
backend-typecheck: ## Run mypy type checking on backend
	@echo "$(YELLOW)Type checking backend code...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run mypy app/

.PHONY: backend-run
backend-run: ## Run backend server locally
	@echo "$(YELLOW)Starting backend server...$(NC)"
	cd $(BACKEND_DIR) && $(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: backend-check
backend-check: backend-lint backend-typecheck backend-test ## Run all backend checks (lint, typecheck, test)
	@echo "$(GREEN)All backend checks passed!$(NC)"

# Frontend Commands
.PHONY: frontend-setup
frontend-setup: ## Set up frontend environment and install dependencies
	@echo "$(YELLOW)Setting up frontend environment...$(NC)"
	cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)Frontend setup complete!$(NC)"

.PHONY: frontend-test
frontend-test: ## Run frontend tests
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && npm test

.PHONY: frontend-lint
frontend-lint: ## Run ESLint on frontend code
	@echo "$(YELLOW)Linting frontend code...$(NC)"
	cd $(FRONTEND_DIR) && npm run lint

.PHONY: frontend-typecheck
frontend-typecheck: ## Run TypeScript type checking on frontend
	@echo "$(YELLOW)Type checking frontend code...$(NC)"
	cd $(FRONTEND_DIR) && npm run type-check

.PHONY: frontend-dev
frontend-dev: ## Run frontend dev server
	@echo "$(YELLOW)Starting frontend dev server...$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

.PHONY: frontend-build
frontend-build: ## Build frontend for production
	@echo "$(YELLOW)Building frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm run build

.PHONY: frontend-check
frontend-check: frontend-lint frontend-typecheck frontend-test ## Run all frontend checks
	@echo "$(GREEN)All frontend checks passed!$(NC)"

# Agent Commands
.PHONY: agent-build
agent-build: ## Build agent Docker image
	@echo "$(YELLOW)Building agent Docker image...$(NC)"
	cd $(AGENT_DIR) && docker build -t claude-agent:local .

.PHONY: agent-run
agent-run: ## Run agent locally with Docker
	@echo "$(YELLOW)Running agent...$(NC)"
	cd $(AGENT_DIR) && docker run -it \
		-e ANTHROPIC_API_KEY=$${ANTHROPIC_API_KEY} \
		-v $$(pwd)/sessions:/sessions \
		claude-agent:local

# Combined Commands
.PHONY: setup
setup: backend-setup frontend-setup ## Set up both frontend and backend environments
	@echo "$(GREEN)All environments set up!$(NC)"

.PHONY: test
test: backend-test frontend-test ## Run all tests
	@echo "$(GREEN)All tests passed!$(NC)"

.PHONY: lint
lint: backend-lint frontend-lint ## Lint all code
	@echo "$(GREEN)All linting passed!$(NC)"

.PHONY: format
format: backend-format ## Format all code
	@echo "$(GREEN)All code formatted!$(NC)"

.PHONY: typecheck
typecheck: backend-typecheck frontend-typecheck ## Type check all code
	@echo "$(GREEN)All type checks passed!$(NC)"

.PHONY: check
check: backend-check frontend-check ## Run all checks (lint, typecheck, test)
	@echo "$(GREEN)All checks passed!$(NC)"

# Docker Commands
.PHONY: docker-up
docker-up: ## Start all services with docker-compose
	@echo "$(YELLOW)Starting services...$(NC)"
	docker-compose -f docker-compose.local.yml up -d

.PHONY: docker-down
docker-down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose -f docker-compose.local.yml down

.PHONY: docker-logs
docker-logs: ## Show logs from all services
	docker-compose -f docker-compose.local.yml logs -f

# Utility Commands
.PHONY: clean
clean: ## Clean up generated files and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Cleanup complete!$(NC)"

.PHONY: install-tools
install-tools: ## Install required development tools
	@echo "$(YELLOW)Installing development tools...$(NC)"
	@which $(UV) > /dev/null || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@which $(PYTHON) > /dev/null || echo "$(RED)Python 3.12 is required. Please install it first.$(NC)"
	@echo "$(GREEN)Tools installed!$(NC)"

# Git Commands
.PHONY: pr-check
pr-check: check ## Run all checks before creating a PR
	@echo "$(YELLOW)Running pre-PR checks...$(NC)"
	@git diff --cached --exit-code || (echo "$(RED)Error: You have staged changes. Commit or unstage them first.$(NC)" && exit 1)
	@git diff --exit-code || (echo "$(RED)Error: You have unstaged changes. Commit or stash them first.$(NC)" && exit 1)
	@echo "$(GREEN)Ready to create PR!$(NC)"

# Default target
.DEFAULT_GOAL := help