.PHONY: help install install-dev test test-verbose coverage clean lint format check build

# Default target
help:
	@echo "PPL - Python People Manager - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo "  make test           Run all tests"
	@echo "  make test-verbose   Run tests with verbose output"
	@echo "  make coverage       Run tests with coverage report"
	@echo "  make clean          Remove build artifacts and cache files"
	@echo "  make lint           Check code style (if linters configured)"
	@echo "  make format         Format code (if formatters configured)"
	@echo "  make check          Run all quality checks (tests + coverage)"
	@echo "  make build          Build distribution packages"

# Install production dependencies
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run all tests
test:
	python -m pytest tests/

# Run tests with verbose output
test-verbose:
	python -m pytest tests/ -v

# Run tests with coverage report
coverage:
	python -m pytest tests/ --cov=ppl --cov-report=term-missing --cov-report=html

# Clean build artifacts and cache files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Lint code (placeholder - add linters as needed)
lint:
	@echo "Linting not configured. Consider adding flake8, pylint, or ruff."
	@echo "Example: pip install flake8 && flake8 ppl/ tests/"

# Format code (placeholder - add formatters as needed)
format:
	@echo "Formatting not configured. Consider adding black or autopep8."
	@echo "Example: pip install black && black ppl/ tests/"

# Run all quality checks
check: test coverage

# Build distribution packages
build: clean
	python -m build
