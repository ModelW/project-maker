.PHONY: format black isort celery_run dev_stack docker_test

PYTHON_BIN ?= poetry run python

format: isort black

black:
	$(PYTHON_BIN) -m black --exclude '/(\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist|node_modules|webpack_bundles)/' .

isort:
	$(PYTHON_BIN) -m isort .

# :: IF api__celery
celery_run:
	poetry run celery --app ___project_name__snake___.django.celery:app worker --loglevel=INFO --beat

# :: ENDIF
dev_stack:
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml up postgres redis --force-recreate --abort-on-container-exit --remove-orphans

docker_test:
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml up --build --force-recreate --abort-on-container-exit --remove-orphans ; python -m webbrowser -t "./bdd/report/results/report.html"