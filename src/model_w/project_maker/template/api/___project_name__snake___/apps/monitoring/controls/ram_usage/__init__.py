"""RAM usage health control."""

from __future__ import annotations

import psutil
from whealth import BaseControl, Failure


class Control(BaseControl):
    """Check that system memory usage stays below a safe threshold."""

    max_usage_percent: float = 90.0
    """Memory usage percentage above which a warning is raised."""

    def get_failures(self) -> list[Failure]:
        """Run the RAM usage health check.

        Returns
        -------
        list[Failure]
            A single warning failure when memory usage is too high,
            otherwise an empty list.
        """
        memory = psutil.virtual_memory()

        if memory.percent < self.max_usage_percent:
            return []

        available_gib = memory.available / (1024**3)
        total_gib = memory.total / (1024**3)

        return [
            Failure(
                key="ram",
                outcome="warning",
                context={
                    "percent": memory.percent,
                    "available_gib": round(available_gib, 2),
                    "total_gib": round(total_gib, 2),
                    "threshold": self.max_usage_percent,
                },
            ),
        ]
