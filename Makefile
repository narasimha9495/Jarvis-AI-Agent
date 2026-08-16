# Jarvis AI — Makefile

.PHONY: install test run lint clean

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

run:
	uvicorn app.main:app --reload --port 8000

lint:
	ruff check app/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
