.PHONY: format black isort procrastinate_run dev_stack destroy_stack performance_test docker_test update-snapshots

PYTHON_BIN ?= poetry run python
# Port to serve the test report on. 0 lets the OS pick a free port (the URL is printed).
REPORT_PORT ?= 0

# Serve the generated test report over HTTP (avoids browser/file:// permission issues).
SERVE_REPORT = python -c "import functools, http.server; h=functools.partial(http.server.SimpleHTTPRequestHandler, directory='./bdd/report/results'); s=http.server.HTTPServer(('127.0.0.1', $(REPORT_PORT)), h); print(f'Serving test report at http://localhost:{s.server_address[1]}/report.html', flush=True); s.serve_forever()"

format: isort black

black:
	$(PYTHON_BIN) -m black --exclude '/(\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist|node_modules|webpack_bundles)/' .

isort:
	$(PYTHON_BIN) -m isort .

procrastinate_run:
	$(PYTHON_BIN) ./manage.py procrastinate worker

dev_stack:
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml up postgres redis --force-recreate --abort-on-container-exit --remove-orphans
# :: IF api__testing
modelw_dev_stack:
	docker compose -p modelw_projectmaker -f ./bdd/_infrastructure/docker-compose-e2e.yaml up postgres redis --force-recreate --abort-on-container-exit --remove-orphans
# :: ENDIF

destroy_stack:
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml down postgres redis
# :: IF api__testing
modelw_destroy_stack:
	docker compose -p modelw_projectmaker -f ./bdd/_infrastructure/docker-compose-e2e.yaml down postgres redis
# :: ENDIF

performance_test:
	./bdd/performance/test_performance.sh
# :: IF api__testing
modelw_docker_test:
	docker compose -p modelw_projectmaker -f ./bdd/_infrastructure/docker-compose-e2e.yaml up --build --force-recreate --abort-on-container-exit --remove-orphans ; $(SERVE_REPORT)
# :: ENDIF

docker_test:
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml up --build --force-recreate --abort-on-container-exit --remove-orphans ; $(SERVE_REPORT)

update-snapshots:
	poetry run pytest -m vr --update-snapshots

tm_dfd:
	cd security && $(PYTHON_BIN) threat_model.py --dfd | dot -Tpng -o dfd.png

tm_seq:
	cd security && $(PYTHON_BIN) threat_model.py --seq | plantuml -tpng -pipe > seq.png

tm_report: tm_dfd tm_seq
	cd security && $(PYTHON_BIN) threat_model.py --report report_template.md > report.md