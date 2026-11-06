"""Procrastinate health control."""

from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from django.conf import settings
from whealth import BaseControl, Failure


def _get_app() -> Any:
    """Return the Procrastinate app to check.

    Uses ``settings.PROCRASTINATE_APP`` when defined, and falls back to the
    default Django Procrastinate app otherwise.
    """
    configured = getattr(settings, "PROCRASTINATE_APP", None)

    if configured is not None:
        return configured

    from procrastinate.contrib.django import app

    return app


class Control(BaseControl):
    """Check that Procrastinate can reach its database and worker app."""

    def get_failures(self) -> list[Failure]:
        """Run the Procrastinate health check.

        Returns
        -------
        list[Failure]
            A single error failure when Procrastinate is not reachable,
            otherwise an empty list.
        """
        from procrastinate import exceptions
        from procrastinate.contrib.django.healthchecks import healthchecks

        try:
            async_to_sync(healthchecks)(app=_get_app())
        except exceptions.ConnectorException as e:
            return [
                Failure(
                    key="procrastinate",
                    outcome="error",
                    context={
                        "reason": "Error connecting to Procrastinate database",
                        "error": str(e),
                    },
                ),
            ]
        except Exception as e:
            return [
                Failure(
                    key="procrastinate",
                    outcome="error",
                    context={
                        "reason": "Error checking Procrastinate",
                        "error": str(e),
                    },
                ),
            ]

        return []
