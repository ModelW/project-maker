from ___project_name__snake___.django.celery import app

from .models import Event
from .resolver import build_resolver


@app.task
def log_beat():
    """
    Log that the beat is running.
    """

    Event.objects.create(
        event_type="beat",
        is_success=True,
        data={},
    )


@app.task
def clear_log():
    """
    Delete old items from the events log
    """

    Event.objects.exclude(pk__in=Event.objects.within(weeks=1).values("pk")).delete()


@app.task
def log_entry(**kwargs):
    """
    Because sometimes there is no DB access at the time of collecting the log,
    we allow to create them through this task

    Specifically, when we try to create an event while the DB connection to
    TMSA is failing, it seems like the data is never committed. Instead of
    dealing with shenanigans of the ORM, we just send the event through here.

    Parameters
    ----------
    kwargs
        Arguments for log creation
    """

    Event.objects.create(**kwargs)


@app.task
def check_status():
    """
    Periodic check of status to keep track of status history
    """

    resolver = build_resolver()
    resolver.check()
