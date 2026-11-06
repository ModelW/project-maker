## Testing

- Fast suite (generates every option combination, static checks + ruff):
  `poetry run pytest -q` (~105s, timeout 400000ms)
- Slow tier (real `poetry lock`, API install + TS client generation, generated
  front's pnpm install/lint/check/test/build, then starts the projects: API
  runserver + front dev server):
  `PM_TEST_DATABASE_URL=postgresql://pm_test:pm_test@localhost:5434/postgres poetry run pytest -m slow -q`
  (~210s, network-dependent, timeout 900000ms). Needs Java, local Redis and a
  PostgreSQL role allowed to create databases (`pm_test` on the PG16 cluster,
  port 5434); without the variable, the API start checks are skipped. Ports
  3000 and 8000 must be free. CI runs it on Linux, macOS and Windows.
- Raw template e2e (Docker):
  `docker compose -f src/model_w/project_maker/template/api/bdd/_infrastructure/docker-compose-e2e.yaml up --build --abort-on-container-exit --remove-orphans`
  (~3min once images are built, timeout 1200000ms). Results in
  `src/model_w/project_maker/template/api/bdd/report/results/`.
- Static: `make lint` (ruff on the project maker, `ruff format --check` on the
  template API, prettier on the template front; the raw template only needs to
  be formattable).
- Always: redirect output to a temp file; silent on success; dump failures only.
- Last measured: 2026-11-04, fast 105s, slow 157s, e2e 171s.
