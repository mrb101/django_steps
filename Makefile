.PHONY: help install dev-install test run migrate clean build publish docs-build docs-serve

help:
	@echo "Available commands:"
	@echo "  install      Install the package in editable mode"
	@echo "  dev-install  Install with development dependencies"
	@echo "  test         Run tests"
	@echo "  run          Run the example Django server"
	@echo "  migrate      Run Django migrations"
	@echo "  clean        Clean up build artifacts"
	@echo "  build        Build the package"
	@echo "  publish      Publish to PyPI"
	@echo "  docs-build   Build the documentation"
	@echo "  docs-serve   Serve the documentation locally"

install:
	uv add . --dev

dev-install:
	uv add .[dev] --dev

test:
	uv run pytest

run:
	cd example && uv run python manage.py runserver

migrate:
	cd example && uv run python manage.py migrate

makemigrations:
	cd example && uv run python manage.py makemigrations

shell:
	cd example && uv run python manage.py shell

superuser:
	cd example && uv run python manage.py createsuperuser

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	uv build

publish:
	uv publish

docs-build:
	uv add .[docs] --dev
	cd docs && uv run sphinx-build -b html . _build/html

docs-serve:
	cd docs/_build/html && uv run python -m http.server 8080
