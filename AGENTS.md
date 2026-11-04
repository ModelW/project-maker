## Testing

- Fast suite (generates every option combination, static checks + ruff):
  `poetry run pytest -q` (~105s, timeout 400000ms)
- Slow tier (real `poetry lock`, API install + TS client generation, generated
  front's pnpm install/lint/check/test/build): `poetry run pytest -m slow -q`
  (~160s, network-dependent, timeout 900000ms)
- Raw template e2e (Docker):
  `docker compose -f src/model_w/project_maker/template/api/bdd/_infrastructure/docker-compose-e2e.yaml up --build --abort-on-container-exit --remove-orphans`
  (~3min once images are built, timeout 1200000ms). Results in
  `src/model_w/project_maker/template/api/bdd/report/results/`.
- Static: `make lint` (ruff on the project maker, `ruff format --check` on the
  template API, prettier on the template front; the raw template only needs to
  be formattable).
- Always: redirect output to a temp file; silent on success; dump failures only.
- Last measured: 2026-11-04, fast 105s, slow 157s, e2e 171s.
