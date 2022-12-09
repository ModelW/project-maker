from pathlib import Path
from typing import Mapping, Sequence

from black import Mode, format_file_in_place
from isort import Config
from isort.main import sort_imports
from pathspec import pathspec
from tomlkit import dumps, inline_table, parse

from ._base import BaseComponent


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
    Tweaking a bit the project's .gitignore to include only API-related files
    and exclude the initial "people" migration (we want to keep it locally
    because we need it for development but at the same time we don't want to
    impose on the developer a user model out of the box).
    """

    lines = [
        "*",
        "!/api/",
    ]

    with open(Path(__file__).parent.parent / "template" / ".gitignore") as f:
        lines.extend(f)

    lines.append("poetry.lock")
    lines.append("api/src/___project_name__snake___/people/migrations/0001_initial.py")

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


class ApiComponent(BaseComponent):
    path_specs = make_path_specs()

    def __init__(self, black_mode: Mode, isort_config: Config):
        self.black_mode = black_mode
        self.isort_config = isort_config

    def accept(self, path: Path, context: Mapping):
        if not context["api"]["enable"]:
            return False

        if self.path_specs.match_file(path):
            return False

        try:
            sub_path = path.relative_to("api/src/___project_name__snake___")
        except ValueError:
            sub_path = None

        if not context["api"]["channels"]:
            if any(
                [
                    sub_path == Path("django/routing.py"),
                    sub_path == Path("django/asgi.py"),
                ]
            ):
                return False

        if not context["api"]["celery"]:
            if sub_path == Path("django/celery.py"):
                return False

        if not context["api"]["wagtail"]:
            if sub_path and Path("cms") in sub_path.parents:
                return False

        return True

    def post_process(self, root: Path, path: Path, context: Mapping) -> None:
        """
        Mostly running black and isort on the project so that it comes out
        clean when generated.

        Also takes care of manage.py's chmod, renaming .env and other small
        details of that sort we might want to address.
        """

        file_path = root / path

        if path == Path("api/manage.py") or path == Path("api/pmanage"):
            file_path.chmod(0o755)

        if path.name.endswith(".py"):
            format_file_in_place(src=file_path, mode=self.black_mode, fast=False)
            sort_imports(file_name=f"{file_path}", config=self.isort_config)

        if path == Path("api/pyproject.toml"):
            clean_pyproject(file_path)

        if file_path.name == ".env-template":
            new_path = file_path.parent / ".env"
            file_path.rename(new_path)
