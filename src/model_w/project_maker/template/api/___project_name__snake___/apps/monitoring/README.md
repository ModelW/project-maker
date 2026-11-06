# Monitoring

This app hosts the project's [Whealth](https://github.com/ModelW/whealth)
health checks. Whealth is the Model W health-checking framework: it discovers
small "controls", runs them, stores the results in the database, and exposes
them through JSON and HTML endpoints (mounted at `back/whealth/`).

Nothing business-related should live here — this app is only about
infrastructure health. Business-specific controls should live in the app they
belong to (any installed Django app can host controls, see
[Where to put a control](#where-to-put-a-control)).

## Registered controls

Whealth ships a few built-in controls, and this app adds two more:

| Key                      | What it checks                                       |
| ------------------------ | ---------------------------------------------------- |
| `whealth.database`       | every configured DB connection answers `SELECT 1`    |
| `whealth.cache`          | every configured cache backend is reachable          |
| `whealth.storage`        | every configured storage backend is reachable        |
| `whealth.crons`          | registered cron tasks check in on schedule           |
| `monitoring.ram_usage`   | container memory usage stays below 90%               |
| `monitoring.procrastinate` | Procrastinate can reach its DB and its apps        |

## How Whealth works

- **Discovery**: on first use, Whealth scans every installed Django app for a
  `controls/` directory. Each sub-directory that looks like a control is
  imported and validated.
- **Controls**: a control is a class whose `get_failures()` returns a list of
  `Failure` objects. An **empty list means "everything is fine"** — controls
  only report problems.
- **Running**: a periodic Procrastinate task (`whealth.tasks.run_controls`)
  runs **all** controls every minute, in dependency order, and writes the
  outcome to the database (`whealth.RunRecord` for the whole pass,
  `whealth.Incident` for individual failures).
- **Serving**: the HTTP endpoints normally serve the **most recent run from the
  database**. They only run the controls live when the cached run is older than
  `WHEALTH_RUN_MAX_AGE` (default 1m10s). So in the happy path, hitting the
  health URL is just a database read.
- **Failure outcomes**: `warning` (degraded but operational), `error` (broken),
  `internal_error` (the control itself crashed).
- **Dependencies**: a control can declare `depends_on` other controls. If a
  dependency has an `error`/`internal_error`, the dependent control is skipped
  instead of producing misleading results.

> **Keep controls fast.** Every control runs within the single per-minute pass
> and within any live HTTP run. A control that takes seconds is fine; a control
> that takes minutes needs special handling (see
> [Checks that are slow](#checks-that-are-slow-eg-2-minutes)).

## Where to put a control

In any **installed** app, create `controls/<slug>/`. By convention:

- infrastructure checks → `apps/monitoring/controls/`
- business checks → the app that owns the data/logic, e.g.
  `apps/<domain>/controls/`

Control slugs must be unique **per app**, since a control is addressed as
`app_label.slug` (e.g. `monitoring.ram_usage`).

## Anatomy of a control

```
apps/monitoring/controls/<slug>/
├── __init__.py    # contains exactly one Control(BaseControl) class
├── manifest.yaml  # metadata: title, depends_on, is_ignorable
└── README.md      # human documentation (surfaced in the admin)
```

### `__init__.py`

The module must contain **exactly one** `BaseControl` subclass, and it must be
named `Control` by convention:

```python
"""Disk usage health control."""

from __future__ import annotations

import psutil
from whealth import BaseControl, Failure


class Control(BaseControl):
    """Warn when the root filesystem is almost full."""

    max_usage_percent: float = 90.0

    def get_failures(self) -> list[Failure]:
        """Run the disk usage check."""
        usage = psutil.disk_usage("/")

        if usage.percent < self.max_usage_percent:
            return []

        return [
            Failure(
                key="/",
                outcome="warning",
                context={"percent": usage.percent},
            ),
        ]
```

Notes:

- `key` identifies a single failure within the control. Use one `Failure` per
  affected entity (per database alias, per disk, per task name, ...) so
  incidents can be tracked and ignored individually.
- `context` is arbitrary JSON stored with the incident and shown in the admin.
  Use it to carry the numbers that justify the failure.
- Failures **must be stable and ordered** so results can be compared across
  runs.
- If the control can suggest a fix, implement `get_remediation()`:

  ```python
  from whealth import BaseControl, Failure, RestartRemediation


  class Control(BaseControl):
      def get_failures(self) -> list[Failure]:
          ...

      def get_remediation(self, failure: Failure) -> RestartRemediation | None:
          return RestartRemediation(components=["api"])
  ```

  `RestartRemediation` powers the `back/whealth/should-restart/<service>.json`
  endpoint; other options are `PyRemediation` and `SuggestionRemediation`.

### `manifest.yaml`

```yaml
title: Disk Usage
depends_on:
    - whealth.database
```

- `title` is the human-readable name (defaults to the slug).
- `depends_on` lists `app_label.slug` references. Entries without a dot refer to
  the same app.
- `is_ignorable` (default `true`) controls whether the control's incidents can
  be ignored from the admin. When `true`, Whealth **automatically adds a
  dependency on `whealth.database`** (because ignoring needs the DB). Set it to
  `false` for checks that genuinely don't touch the database, so a database
  outage doesn't skip them:

  ```yaml
  title: RAM Usage
  depends_on: []
  is_ignorable: false
  ```

### `README.md`

Free-form Markdown describing the check, its logic and how to troubleshoot it.
It is synced into the database and displayed in the admin.

## Adding a check

1. Create the directory:

   ```bash
   mkdir -p apps/monitoring/controls/disk_usage
   ```

2. Add `__init__.py`, `manifest.yaml` and `README.md` as shown above.

3. Validate that Whealth can load it and that dependencies are consistent:

   ```bash
   python manage.py list_controls
   ```

4. Run everything (including your new control) once:

   ```bash
   python manage.py run_controls
   ```

That's it — the control is now part of the per-minute run and appears in the
`back/whealth/` endpoints.

## Checks that are slow

**Short answer:** if a check takes time, don't do the work inside
`get_failures()`. Run the work on its own schedule and have the control read the
stored result.

Why: Whealth runs every control **synchronously** in two places:

1. the per-minute `run_controls` task, and
2. the HTTP request itself, whenever the cached run is older than
   `WHEALTH_RUN_MAX_AGE`.

A 2-minute control would therefore make the per-minute task overlap with itself
and would block health requests for ~2 minutes whenever the cache is stale. Not
great.

### Recommended: compute off to the side, read in the control

Create a model to store the last result (this adds a `migrations/` directory to
the app the first time you do this):

```python
# apps/monitoring/models.py
from django.db import models


class AuditResult(models.Model):
    date_checked = models.DateTimeField(auto_now=True)
    is_healthy = models.BooleanField()
    details = models.JSONField(default=dict)
```

Run the slow work from a dedicated periodic task on a slower schedule, using
Whealth's `procrastinate_task` helper so the task itself gets a cron check-in
(monitored by `whealth.crons`):

```python
# apps/monitoring/tasks.py
from procrastinate.contrib.django import app
from whealth import procrastinate_task
from whealth.procrastinate import ProcrastinateCron

from .models import AuditResult


@procrastinate_task(
    app=app,
    cron=ProcrastinateCron(expression="*/15 * * * *"),
)
def run_audit(timestamp: int) -> None:
    """Run the slow audit (can take minutes) and store its result."""
    healthy, details = do_the_slow_thing()  # ~2 minutes
    AuditResult.objects.update_or_create(
        pk=1,
        defaults={"is_healthy": healthy, "details": details},
    )
```

Then the control is trivial and fast — it just reports the stored state, and
raises a `warning`/`error` when the result is missing, unhealthy, or stale:

```python
# apps/monitoring/controls/audit/__init__.py
from __future__ import annotations

from datetime import timedelta

from django.utils.timezone import now
from whealth import BaseControl, Failure

from ...models import AuditResult

MAX_AGE = timedelta(minutes=45)


class Control(BaseControl):
    """Report the outcome of the periodic audit."""

    def get_failures(self) -> list[Failure]:
        """Read the last audit result."""
        try:
            result = AuditResult.objects.get(pk=1)
        except AuditResult.DoesNotExist:
            return [Failure(key="missing", outcome="error")]

        if now() - result.date_checked > MAX_AGE:
            return [
                Failure(
                    key="stale",
                    outcome="warning",
                    context={"last_checked": result.date_checked.isoformat()},
                ),
            ]

        if not result.is_healthy:
            return [
                Failure(key="unhealthy", outcome="error", context=result.details),
            ]

        return []
```

## Endpoints

Mounted at `back/whealth/` (see `django/urls.py`):

| URL                                         | Purpose                                          |
| ------------------------------------------- | ------------------------------------------------ |
| `back/whealth/recap.html`                   | HTML recap of the latest run (staff permission)  |
| `back/whealth/control.json`                 | `{"ok": true/false}` for all controls            |
| `back/whealth/control/<app>/<slug>.json`    | `{"ok": true/false}` for one control             |
| `back/whealth/control/<app>/<slug>/deep.json` | same, but also requires its dependencies to be OK |
| `back/whealth/should-restart/<service>.json` | whether restarting `service` would fix something |

All JSON endpoints return HTTP `200` when OK and `418` when not, which makes
them convenient for load balancers and orchestrators.

## Useful management commands

```bash
python manage.py list_controls        # list + validate controls and dependencies
python manage.py run_controls         # run all controls now and sync to the DB
python manage.py get_control_routes   # print every control's URLs as JSON
```

## Settings

| Setting                     | Default         | Purpose                                                            |
| --------------------------- | --------------- | ------------------------------------------------------------------ |
| `WHEALTH_RUN_MAX_AGE`       | `1m10s`         | max age of a cached run before HTTP requests trigger a live run    |
| `WHEALTH_RUN_LOG_RETENTION` | `365 days`      | how long `RunRecord` rows are kept (pruned by a daily task)        |
| `WHEALTH_BASE_URL`          | `BASE_URL`      | base URL used by `get_control_routes` when printing absolute URLs  |
