.PHONY: help install dev test lint format type-check security clean examples doc-coverage mutate docs check

# Mutation score floor for the tool handlers: 99.3% (302 of 304) on
# 2026-09-19; the two survivors only change the case of an HTTP header
# name, which is equivalent. The floor sits under the score so an SDK or
# library release cannot block a release on a handful of mutants. Keep
# it in step with .github/workflows/mutation.yml.
MUTATION_FLOOR ?= 90

PYTHON ?= python3
POETRY ?= poetry

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(POETRY) install --only main

dev: ## Install all dependencies (including dev)
	$(POETRY) install

test: ## Run tests
	$(POETRY) run pytest tests/ -v

lint: ## Run linters (ruff + black check)
	$(POETRY) run ruff check acmt001_mcp/ tests/
	$(POETRY) run black --check acmt001_mcp/ tests/

format: ## Auto-format code (ruff fix + black)
	$(POETRY) run ruff check --fix acmt001_mcp/ tests/
	$(POETRY) run black acmt001_mcp/ tests/

type-check: ## Run mypy type checking
	$(POETRY) run mypy acmt001_mcp/

security: ## Run security scan (bandit)
	$(POETRY) run bandit -r acmt001_mcp/ -c pyproject.toml 2>/dev/null || \
		$(POETRY) run bandit -r acmt001_mcp/ -ll

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .eggs/ docs/_build/ mutants/ .hypothesis/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
	rm -rf coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

examples: ## Verify example scripts run
	$(POETRY) run python examples/mcp_tools.py

doc-coverage: ## Enforce the 100% docstring coverage gate
	$(POETRY) run interrogate -c pyproject.toml -v acmt001_mcp

# macOS: urllib's proxy lookup (_scproxy) crashes in a forked child, and
# mutmut runs every mutant in one, so the GLEIF tests would die with
# SIGSEGV and drop out of the score. A proxy in the environment makes
# urllib skip that lookup; the tests mock the transport, so nothing is
# ever sent to it. Harmless on Linux, where CI measures the real score.
mutate: export http_proxy ?= http://127.0.0.1:9
mutate: export https_proxy ?= http://127.0.0.1:9
mutate: ## Mutation testing over the tool handlers (mutmut 3, config in pyproject)
	rm -rf mutants
	HYPOTHESIS_PROFILE=mutation $(POETRY) run mutmut run
	$(POETRY) run mutmut export-cicd-stats
	$(POETRY) run python scripts/mutation_gate.py --floor $(MUTATION_FLOOR)

docs: ## Build the Sphinx site into docs/_build/html (warnings are errors)
	$(POETRY) run sphinx-build -W --keep-going -b html docs docs/_build/html

check: lint type-check test doc-coverage examples ## Run all gates
