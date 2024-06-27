from typing import Mapping, Sequence

from health_check.cache.backends import CacheBackend
# :: IF api__celery
from health_check.contrib.celery_ping.backends import CeleryPingHealthCheck
# :: ENDIF
from health_check.contrib.psutil.backends import MemoryUsage
from health_check.db.backends import DatabaseBackend

from .base import DjangoHealthCheckWrapper, HealthCheck, Outcome, Status
from .models import Event


def disp_window(window: Mapping[str, int]) -> str:
    """
    Returns a friendly text for a time window (aka the kwargs of a timedelta)

    Parameters
    ----------
    window
        Window to be displayed
    """

    items = []

    for key, value in window.items():
        if value == 0:
            continue

        if value == 1:
            key = key.rstrip("s")

        items.append(f"{value} {key}")

    return " ".join(items)


def disp_stats(stats: Mapping[str, int]) -> str:
    """
    All the checks relying on the logs use the same pattern of checking how
    many success/failures happened. This is an utility to transform these
    stats into a readable text.

    Parameters
    ----------
    stats
        A dictionary with "success", "failure" and "total" as keys
    """

    success_str, failure_str, total_str = "", "", ""

    if success := stats["success"]:
        plural = "es" if success != 1 else ""
        success_str = f"{success} success{plural}"

    if failure := stats["failure"]:
        plural = "s" if failure != 1 else ""
        failure_str = f"{failure} failure{plural}"

    if total := stats["total"]:
        total_str = f"out of {total}"
    else:
        total_str = "no events"

    part_1 = ", ".join([x for x in [success_str, failure_str] if x])

    return " ".join([x for x in [part_1, total_str] if x]).capitalize()


class Database(DjangoHealthCheckWrapper):
    """
    Checks that the default database can be reached, read and write
    """

    base_class = DatabaseBackend

    def get_resolving_actions(self, outcome: Outcome) -> str:
        return """# __CODE__ &mdash; Database cannot be reached

This checks verifies if the database is reachable by inserting and deleting a
row in a test table.

## Possible causes

- There could be a network issue that prevents to access the database
- The data could be inconsistent or the disk full
- The database server could be overloaded

## Possible solutions

- Check the network connectivity
- Check the disk space
- Check the database server logs
- Check the database server status
"""

    def suggest_reboot(self, outcome: Outcome) -> Sequence[str]:
        return ["database"]

    def get_name(self) -> str:
        return "Database"


class RamUsage(DjangoHealthCheckWrapper):
    """
    Checks that we don't use too much RAM
    """

    base_class = MemoryUsage

    def get_name(self) -> str:
        return "RAM Usage"

    def get_resolving_actions(self, outcome: Outcome) -> str:
        return """# __CODE__ &mdash; RAM usage is too high

The memory usage in the container running the application is too high.

## Possible causes

- There is a memory leak in the application
- The application just needs more RAM

## Possible solutions

- Short term, restart the container
- Long term, identify if this issue comes from a leak (in which case you can
  fix the leak) or if the application just needs more RAM (in which case you
  can increase the RAM allocated to the container)
"""

    def suggest_reboot(self, outcome: Outcome) -> Sequence[str]:
        return ["api"]

# :: IF api__redis

class Cache(DjangoHealthCheckWrapper):
    """
    Validates cache accessibility. Since the queue is also the cache, it will
    validate the queue as well (somehow).
    """

    base_class = CacheBackend

    def get_name(self) -> str:
        return "Cache"

    def get_resolving_actions(self, outcome: Outcome) -> str:
        return """# __CODE__ &mdash; Redis cache cannot be reached

This checks verifies if the cache is reachable by inserting and deleting an
entry in the cache.

## Possible causes

- There could be a network issue that prevents to access the cache
- The cache could be overloaded

## Possible solutions

- Check the network connectivity
- Check the cache server logs
- Check the cache server status
"""

    def suggest_reboot(self, outcome: Outcome) -> Sequence[str]:
        return ["redis"]

# :: ENDIF

# :: IF api__celery
class CeleryPing(DjangoHealthCheckWrapper):
    """
    Validates that Celery is working and replying.
    """

    base_class = CeleryPingHealthCheck

    def get_name(self) -> str:
        return "Celery Ping"

    def get_resolving_actions(self, outcome: Outcome) -> str:
        return """# __CODE__ &mdash; Celery cannot be reached

This test works by sending a ping to the Celery worker and waiting for an
answer. If the answer is not received, it means that the worker is not
reachable.

## Possible causes

- There could be a network issue that prevents reaching out the queue, but
  if the Redis is responding (see the Cache check), it is unlikely that this
  would be an issue
- The Celery worker could be overloaded or all its workers could be busy. This
  is the most likely.
- The worker could be down

## Possible solutions

- Check that the worker is running.
- Check if the process is active. If CPU use is low, it probably means that
  the worker is caught up in some deadlock or network timeout. Simplest
  solution is to restart it.
- If it is _too_ active (100% CPU, 100% RAM), it means that the worker is
  overloaded. In this case, you should increase the number of workers or the
  resources available to the container.
"""

    def suggest_reboot(self, outcome: Outcome) -> Sequence[str]:
        return ["celery_worker"]


class LogBeat(HealthCheck):
    """
    Every minute the beat will trigger a task to write a log. We make sure here
    that these logs are being written.
    """

    WINDOW = dict(minutes=2)

    def get_name(self) -> str:
        return "Celery Beat"

    def get_status(self) -> Outcome:
        stats = Event.objects.type("beat").within(**self.WINDOW).stats()
        stats_str = disp_stats(stats)

        if stats["success"]:
            outcome = dict(
                status=Status.OK,
                message=f"{stats_str} in the last {disp_window(self.WINDOW)}",
            )
        else:
            outcome = dict(
                status=Status.ERROR,
                message=f"{stats_str} in the last {disp_window(self.WINDOW)}",
            )

        return Outcome(
            instance=self,
            **outcome,
        )

    def get_resolving_actions(self, outcome: Outcome) -> str:
        return """# __CODE__ &mdash; Celery beat is not running

This checks verifies if the Celery beat is running by checking if it has
logged a heartbeat in the last 3 minutes.

## Possible causes

- The beat could be down

## Possible solutions

- Check that the beat is running.
"""

    def suggest_reboot(self, outcome: Outcome) -> Sequence[str]:
        return ["celery_beat"]

# :: ENDIF
