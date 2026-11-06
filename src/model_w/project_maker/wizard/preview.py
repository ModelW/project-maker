"""
What the wizard shows about the project before creating it. The files are
computed with the very same rules as the generation, so the preview can't
drift from what gets generated.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path, PurePosixPath

from pathspec import pathspec

from ..generate import TEMPLATE
from ..maker import ApiComponent, BaseComponent, CommonComponent, FrontComponent
from ..maker._base import LOCAL_FILES
from ..template import render_line
from .options import Options

LOCAL_SPEC = pathspec.PathSpec.from_lines("gitignore", LOCAL_FILES)


@cache
def template_files() -> tuple[PurePosixPath, ...]:
    """
    All the files of the template, relative to it, without the local clutter
    (which can be huge, think node_modules).
    """

    out = []

    for dir_path, dir_names, file_names in os.walk(TEMPLATE):
        rel = PurePosixPath(Path(dir_path).relative_to(TEMPLATE).as_posix())
        dir_names[:] = [
            d for d in dir_names if not LOCAL_SPEC.match_file(f"{rel / d}/")
        ]
        out.extend(
            rel / f for f in file_names if not LOCAL_SPEC.match_file(f"{rel / f}")
        )

    return tuple(sorted(out))


def planned_files(context: Mapping, lock: bool = True) -> list[PurePosixPath]:
    """
    Files of the generated project, relative to its root.

    Parameters
    ----------
    context
        Context of the generation
    lock
        Whether the generation locks the API's dependencies (poetry.lock)
    """

    components: list[BaseComponent] = [
        ApiComponent(lock=False),
        FrontComponent(),
        CommonComponent(),
    ]
    out: set[PurePosixPath] = set()

    for sub_path in template_files():
        for component in components:
            if not component.accept(Path(sub_path), context):
                continue

            file_context = component.context(Path(sub_path), context)
            moved = component.target_sub_path(Path(sub_path), file_context)
            target = PurePosixPath(render_line(moved.as_posix(), file_context))
            out.add(target)

            # Created from the template, for the developer to fill
            if target.name == ".env-template":
                out.add(target.with_name(".env"))

    if lock and context["api"]["enable"]:
        out.add(PurePosixPath("api/poetry.lock"))

    return sorted(out)


@dataclass
class Folder:
    """A folder of the preview's file tree"""

    name: str
    folders: dict[str, Folder] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of files in this folder and below"""

        return len(self.files) + sum(f.count for f in self.folders.values())


def file_tree(name: str, files: list[PurePosixPath]) -> Folder:
    """
    Arranges the files as a tree of folders.

    Parameters
    ----------
    name
        Name of the root folder
    files
        Paths relative to the root
    """

    root = Folder(name)

    for path in files:
        folder = root

        for part in path.parts[:-1]:
            folder = folder.folders.setdefault(part, Folder(part))

        folder.files.append(path.name)

    return root


@dataclass(frozen=True)
class Route:
    """Where a part of the single origin goes"""

    path: str
    target: str


def routes(options: Options) -> list[Route]:
    """
    The URLs of the site, all on the same origin.

    Parameters
    ----------
    options
        Wizard's options
    """

    out = []

    if options.front:
        out.append(Route("/", "Front-end pages"))
    elif options.wagtail_enabled:
        out.append(Route("/", "CMS pages, rendered by the API"))

    if options.api:
        admin = f"/back/{options.admin_prefix}"
        out.append(Route(f"{admin}/admin/", "Django admin"))

        if options.wagtail_enabled:
            out.append(Route(f"{admin}/cms/", "Wagtail admin"))

        out.append(Route(f"{admin}/ht/", "Health checks"))
        out.append(Route("/back/api/", "API (/back/api/docs in development)"))

    return out


@dataclass(frozen=True)
class Deployment:
    """What snow.yml deploys (see the template's snow.yml)"""

    components: list[str]
    resources: list[str]


def deployment(options: Options) -> Deployment:
    """
    Summary of the deployment, following the same rules as the template's
    snow.yml.

    Parameters
    ----------
    options
        Wizard's options
    """

    components = []
    resources = []

    if options.api:
        server = "ASGI" if options.channels_enabled else "WSGI"
        components += [
            f"api ({server}, granian)",
            "api-migrate (pre-deploy hook)",
            "api-worker (Procrastinate)",
        ]
        resources.append("PostgreSQL 18")

        if options.wagtail_enabled or options.channels_enabled:
            resources.append("Redis 8")

        if options.wagtail_enabled:
            resources.append("Media bucket (DigitalOcean Spaces)")

    if options.front:
        components.append("front (SvelteKit, Node)")

    return Deployment(components, resources)
