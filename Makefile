.PHONY: install run migrate test superuser lint format seed clean
PYTHON_BIN ?= python3.12
PYTHON := ./venv/bin/python
PIP := ./venv/bin/pip
RUFF := ./venv/bin/ruff
install:

	$(PYTHON_BIN) -m venv --clear venv
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) manage.py runserver

migrate:
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate

test:
	$(PYTHON) manage.py test

superuser:
	$(PYTHON) manage.py createsuperuser

lint:
	$(RUFF) check .

format:
	$(RUFF) format .

seed:
	@echo "Setting up tenants..."
	$(PYTHON) manage.py seed_data
	@echo "\nSeeding demo tenant..."
	$(PYTHON) manage.py tenant_command seed_data --schema=demo

clean:
	find . -type d -name __pycache__ -not -path "./venv/*" -exec rm -rf {} +
	find . -type f -name "*.pyc" -not -path "./venv/*" -delete
