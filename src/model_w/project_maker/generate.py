"""
Builds the generation's context and the Maker, independently from the user
interface (the wizard and the tests use them alike).
"""

import shlex
import string
from collections.abc import Mapping
from pathlib import Path
from random import SystemRandom

from .maker import (
    ApiComponent,
    CommonComponent,
    FrontComponent,
    Maker,
    PrettierComponent,
)
from .words import random_slug

#: The project template
TEMPLATE = Path(__file__).parent / "template"


def generate_random_key(length: int = 50):
    """
    Generates the Django SECRET_KEY setting.

    Parameters
    ----------
    length
        The length of the key to generate.
    """

    return "".join(
        SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(length)
    )


def build_context(
    *,
    project_name: Mapping,
    front: bool,
    api: bool,
    wagtail: bool = False,
    channels: bool = False,
    demo_snippet: bool = False,
    admin_prefix: str | None = None,
    dev_id: str,
    secret_key: str | None = None,
) -> dict:
    """
    Builds the template context from the user's choices.

    This is the single place where derived flags (``wsgi``, ``redis``,
    ``procrastinate``) are computed, so that the interactive wizard and the
    automated tests generate projects from exactly the same context.

    Parameters
    ----------
    project_name
        Declinations of the project name, as returned by
        ``generate_declinations()`` plus the ``initial`` key
    front
        Whether to generate the front-end
    api
        Whether to generate the back-end
    wagtail
        Whether the back-end ships Wagtail (ignored without back-end)
    channels
        Whether the back-end ships Channels (ignored without back-end)
    demo_snippet
        Whether to ship the demo snippet (ignored without Wagtail)
    admin_prefix
        Hides the admin URLs: the Django admin, the CMS (with Wagtail) and the
        health checks live under /back/<admin_prefix>/. Two random words if
        not provided (ignored without back-end).
    dev_id
        "Name <email>" of the developer
    secret_key
        Django secret key, randomly generated if not provided
    """

    if secret_key is None:
        key = generate_random_key()
        secret_key = shlex.quote(f"{key[:25]}wesh{key[25:]}")

    wagtail = api and wagtail
    channels = api and channels

    context = dict(
        secret_key=secret_key,
        front=dict(enable=front),
        api=dict(enable=api),
        project_name=dict(project_name),
        project_title=project_name["natural"],
        dev_id=dev_id,
    )

    if api:
        context["api"].update(
            wagtail=wagtail,
            channels=channels,
            wsgi=not channels,
            redis=wagtail or channels,
            # Make procrastinate mandatory, as health check will need it.
            # When health check is it's own library, this can be removed, and
            # we can bring it in with the health check app.
            procrastinate=True,
            demo_snippet=wagtail and demo_snippet,
        )
        context["admin_prefix"] = admin_prefix or random_slug()

    return context


def build_maker(*, lock: bool = True, ts_client: bool | None = None) -> Maker:
    """
    Builds the Maker with all the components.

    Parameters
    ----------
    lock
        Whether to run ``poetry lock`` on the generated API. Tests disable it
        to avoid hitting the network for every generated project.
    ts_client
        Whether to regenerate the front's TypeScript client from the API's
        schema (installs the API). Defaults to ``lock``.
    """

    return Maker(
        [
            ApiComponent(lock=lock, ts_client=ts_client),
            FrontComponent(),
            CommonComponent(),
            # Last, to format everything once all the files are there
            PrettierComponent(),
        ]
    )
