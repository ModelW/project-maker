import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from pathspec import pathspec
from tomlkit import dumps, inline_table, parse

from ..errors import ProjectMakerError
from ._base import LOCAL_FILES, BaseComponent, Exec


def strip_copy(x):
    if isinstance(x, str):
        return x
    elif isinstance(x, Sequence):
        return [strip_copy(y) for y in x]
    elif isinstance(x, Mapping):
        t = inline_table()
        t.update({strip_copy(k): strip_copy(v) for k, v in x.items()})
        return t
    else:
        return x


def clean_pyproject(path: Path) -> None:
    with open(path) as f:
        data = parse(f.read())

    for section_key in ["dependencies", "dev-dependencies"]:
        try:
            section = data["tool"]["poetry"][section_key]
        except KeyError:
            pass
        else:
            to_update = {}

            for package, spec in section.items():
                if "extras" in spec:
                    if spec["extras"]:
                        spec["extras"] = strip_copy(spec["extras"])
                    else:
                        del spec["extras"]

                to_update[package] = strip_copy(spec)

            section.update(to_update)

    with open(path, "w") as f:
        f.write(dumps(data))


def make_path_specs() -> pathspec.PathSpec:
    """
    Include only API-related files, excluding local files (see LOCAL_FILES)
    and some "project maker only" files which we want to keep locally for
    development but not include in user projects.
    """

    lines = [
        "*",
        "!/api/",
    ]

    lines.extend(LOCAL_FILES)

    lines.append("poetry.lock")
    lines.append("0004_project_maker_only.py")
    lines.append("demo.py")

    return pathspec.PathSpec.from_lines("gitignore", lines)


class ApiComponent(BaseComponent):
    path_specs = make_path_specs()

    def __init__(self, lock: bool = True, ts_client: bool | None = None):
        """
        Parameters
        ----------
        lock
            Run ``poetry lock`` once the project is generated. The lock
            depends on the extras selected by the options, so it can't be
            shipped with the template.
        ts_client
            Install the API and regenerate the front's TypeScript client from
            its OpenAPI schema (needs the lock). Defaults to ``lock``.
        """

        self.lock = lock
        self.ts_client = lock if ts_client is None else ts_client

        self.wagtail_ignore = pathspec.PathSpec.from_lines(
            "gitignore",
            [
                "/api/___project_name__snake___/apps/cms/",
            ],
        )
        self.demo_snippet_ignore = pathspec.PathSpec.from_lines(
            "gitignore",
            [
                "/api/___project_name__snake___/apps/cms/snippets.py",
                "/api/___project_name__snake___/apps/cms/migrations/0003_demosnippet.py",
            ],
        )
        self.front_ignore = pathspec.PathSpec.from_lines(
            "gitignore",
            [
                "/api/bdd/performance/",
                "/api/bdd/_infrastructure/docker-compose-run.yaml",
                "/api/bdd/features/a11y.feature",
                "/api/___project_name__snake___/apps/people/management/",
                "/api/bdd/features/visual_regressions.feature",
            ],
        )
        self.channels_ignore = pathspec.PathSpec.from_lines(
            "gitignore",
            [
                "/api/___project_name__snake___/apps/realtime/",
                "/api/___project_name__snake___/django/routing.py",
                "/api/___project_name__snake___/django/asgi.py",
            ],
        )

    def accept(self, path: Path, context: Mapping):
        if not context["api"]["enable"]:
            return False

        if self.path_specs.match_file(path):
            return False

        if not context["api"]["channels"]:
            if self.channels_ignore.match_file(path):
                return False

        if not context["api"]["wagtail"]:
            if self.wagtail_ignore.match_file(path):
                return False

        # Performance, accessibility and visual tests are about the front
        if not context["front"]["enable"]:
            if self.front_ignore.match_file(path):
                return False

        if not context["api"].get("demo_snippet"):
            if self.demo_snippet_ignore.match_file(path):
                return False

        return True

    def post_process(self, root: Path, path: Path, context: Mapping) -> None:
        """
        Takes care of manage.py's chmod, renaming .env and other small
        details of that sort we might want to address. Formatting happens
        once for the whole project in finalize().
        """

        file_path = root / path

        if path == Path("api/manage.py") or path == Path("api/pmanage"):
            file_path.chmod(0o755)

        if path == Path("api/pyproject.toml"):
            clean_pyproject(file_path)

        if file_path.name == ".env-template":
            new_path = file_path.parent / ".env"

            with (
                open(new_path, "w", encoding="utf-8") as f,
                open(file_path, encoding="utf-8") as g,
            ):
                f.write(g.read())

    def finalize(self, root: Path, context: Mapping) -> None:
        """
        The template only guarantees valid syntax, so we let Ruff auto-fix and
        format the generated API (using the generated pyproject.toml config)
        so that it comes out lint-clean. Then the lockfile gets created for
        the selected extras.
        """

        if not context["api"]["enable"]:
            return

        api = root / "api"
        e = Exec(api)

        # No cache, which would otherwise be left behind in the project
        ruff = [sys.executable, "-m", "ruff"]
        e.exec([*ruff, "check", "--no-cache", "--fix", "--exit-zero", "."])
        e.exec([*ruff, "format", "--no-cache", "."])

        if self.lock:
            env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}

            try:
                e.exec(["poetry", "lock"], env=env)
            except ProjectMakerError as err:
                msg = f"Could not lock API dependencies: {err}"
                raise ProjectMakerError(msg) from err

        if self.ts_client and context["front"]["enable"]:
            self.generate_ts_client(e, env)

    def generate_ts_client(self, e: Exec, env: Mapping[str, str]) -> None:
        """
        The template ships a client generated from its own schema, but the
        project's one is regenerated so that it matches the project exactly.
        This requires installing the API, which the developer will need to do
        anyway. Formatting is done by the front-end component.

        Parameters
        ----------
        e
            Executor in the API directory
        env
            Environment for poetry
        """

        # The schema URL only exists in debug, and nothing else is needed to
        # run the command, hence the build mode
        env = {**env, "BUILD_MODE": "yes", "DEBUG": "yes"}

        # The .env (created from .env-template) takes precedence over the
        # environment and expects real values (storage...), so it's set aside
        # to only rely on the build defaults.
        dotenv = e.cwd / ".env"
        dotenv_aside = e.cwd / ".env.generating"

        try:
            e.exec(["poetry", "install", "--no-interaction"], env=env)

            if dotenv.exists():
                dotenv.rename(dotenv_aside)

            e.exec(
                ["poetry", "run", "python", "manage.py", "generate_ts_client"],
                env=env,
            )
        except ProjectMakerError as err:
            msg = f"Could not generate the TypeScript client: {err}"
            raise ProjectMakerError(msg) from err
        finally:
            if dotenv_aside.exists():
                dotenv_aside.rename(dotenv)
