.PHONY: help install install-dev clean test lint format docs run build publish

# Default target
help:
	@echo "KURSORIN Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  install        Install package in production mode"
	@echo "  install-dev    Install package in development mode"
	@echo "  clean          Remove build artifacts and cache"
	@echo ""
	@echo "Development:"
	@echo "  test           Run test suite"
	@echo "  test-cov       Run tests with coverage report"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  type-check     Run type checking with mypy"
	@echo ""
	@echo "Documentation:"
	@echo "  docs           Build documentation"
	@echo "  docs-serve     Serve documentation locally"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  build          Build distribution packages"
	@echo "  publish        Publish to PyPI"
	@echo ""
	@echo "Run:"
	@echo "  run            Run KURSORIN application"
	@echo "  run-cli        Run KURSORIN CLI"
	@echo "  benchmark      Run performance benchmarks"

# Python executable
PYTHON := python3
PIP := pip3

# Virtual environment
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# Create virtual environment
$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip setuptools wheel

# Install for production
install: $(VENV)/bin/activate
	$(VENV_PIP) install -e .

# Install for development
install-dev: $(VENV)/bin/activate
	$(VENV_PIP) install -e ".[dev,docs]"
	$(VENV_PYTHON) -m pre_commit install

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	rm -rf site/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg" -delete

# Run tests
test:
	$(VENV_PYTHON) -m pytest tests/ -v

# Run tests with coverage
test-cov:
	$(VENV_PYTHON) -m pytest tests/ -v --cov=kursorin --cov-report=term-missing --cov-report=html

# Lint code
lint:
	$(VENV_PYTHON) -m flake8 kursorin/ tests/
	$(VENV_PYTHON) -m pylint kursorin/

# Format code
format:
	$(VENV_PYTHON) -m black kursorin/ tests/ examples/
	$(VENV_PYTHON) -m isort kursorin/ tests/ examples/

# Type checking
type-check:
	$(VENV_PYTHON) -m mypy kursorin/

# Build documentation
docs:
	$(VENV_PYTHON) -m mkdocs build

# Serve documentation locally
docs-serve:
	$(VENV_PYTHON) -m mkdocs serve

# Build distribution packages
build: clean
	$(VENV_PYTHON) -m pip install --upgrade build
	$(VENV_PYTHON) -m build

# Publish to PyPI
publish: build
	$(VENV_PYTHON) -m pip install --upgrade twine
	$(VENV_PYTHON) -m twine upload dist/*

# Run application
run:
	$(VENV_PYTHON) -m kursorin

# Run CLI
run-cli:
	$(VENV_PYTHON) -m kursorin.cli

# Run benchmarks
benchmark:
	$(VENV_PYTHON) scripts/benchmark.py

# Profile performance
profile:
	$(VENV_PYTHON) -m cProfile -o profile.stats -m kursorin --profile
	$(VENV_PYTHON) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(30)"

# Docker build
docker-build:
	docker build -t kursorin:latest -f docker/Dockerfile .

# Docker run
docker-run:
	docker run -it --rm \
		--device=/dev/video0 \
		-e DISPLAY=$(DISPLAY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		kursorin:latest
