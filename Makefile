.PHONY: install dev start test lint check demo docker-up docker-down clean

install:
	python -m pip install -e '.[dev]'

dev:
	music-studio start --reload

start:
	music-studio start

test:
	pytest

lint:
	ruff check .

check: lint test

demo:
	python scripts/create_demo.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
