.PHONY: format lint ts_client procrastinate_run dev_stack destroy_stack performance_test docker_test update-snapshots

PYTHON_BIN ?= poetry run python
# Port to serve the test report on. 0 lets the OS pick a free port (the URL is printed).
REPORT_PORT ?= 0

# Serve the generated test report over HTTP (avoids browser/file:// permission issues).
SERVE_REPORT = python -c "import functools, http.server; h=functools.partial(http.server.SimpleHTTPRequestHandler, directory='./bdd/report/results'); s=http.server.HTTPServer(('127.0.0.1', $(REPORT_PORT)), h); print(f'Serving test report at http://localhost:{s.server_address[1]}/report.html', flush=True); s.serve_forever()"

format:
	$(PYTHON_BIN) -m ruff check --fix .
	$(PYTHON_BIN) -m ruff format .

lint:
	$(PYTHON_BIN) -m ruff format --check .
	$(PYTHON_BIN) -m ruff check .

# :: IF front__enable
# Regenerate the front's API client (front/src/lib/api/client) from the Ninja
# OpenAPI schema, then format it. Run it whenever an endpoint or a schema
# changes, and commit the result.
ts_client:
	DEBUG=yes $(PYTHON_BIN) ./manage.py generate_ts_client
	cd ../front && pnpm exec prettier --write src/lib/api/client/
# :: ENDIF

procrastinate_run:
	$(PYTHON_BIN) ./manage.py procrastinate worker

dev_stack:
# :: IF api__redis
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml up postgres redis --force-recreate --abort-on-container-exit --remove-orphans
# :: ENDIF
# :: IFNOT api__redis
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml up postgres --force-recreate --abort-on-container-exit --remove-orphans
# :: ENDIF
# :: IF api__testing
modelw_dev_stack:
# :: IF api__redis
	docker compose -p modelw_projectmaker -f ./bdd/_infrastructure/docker-compose-e2e.yaml up postgres redis --force-recreate --abort-on-container-exit --remove-orphans
# :: ENDIF
# :: IFNOT api__redis
	docker compose -p modelw_projectmaker -f ./bdd/_infrastructure/docker-compose-e2e.yaml up postgres --force-recreate --abort-on-container-exit --remove-orphans
# :: ENDIF
# :: ENDIF

destroy_stack:
# :: IF api__redis
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml down postgres redis
# :: ENDIF
# :: IFNOT api__redis
	docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-e2e.yaml down postgres
# :: ENDIF
# :: IF api__testing
modelw_destroy_stack:
# :: IF api__redis
	docker compose -p modelw_projectmaker -f ./bdd/_infrastructure/docker-compose-e2e.yaml down postgres redis
# :: ENDIF
# :: IFNOT api__redis
	docker compose -p modelw_projectmaker -f ./bdd/_infrastructure/docker-compose-e2e.yaml down postgres
# :: ENDIF
# :: ENDIF

# :: IF front__enable
performance_test:
	./bdd/performance/test_performance.sh
# :: ENDIF
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