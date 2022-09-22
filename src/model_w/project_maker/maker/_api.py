from pathlib import Path
from typing import Mapping, Sequence

from black import Mode, format_file_in_place
from isort import Config
from tomlkit import parse, dumps, inline_table
from isort.main import sort_imports

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

    for section_key in ['dependencies', 'dev-dependencies']:
        try:
            section = data['tool']['poetry'][section_key]
        except KeyError:
            pass
        else:
            to_update = {}

            for package, spec in section.items():
                if 'extras' in spec:
                    if spec['extras']:
                        spec['extras'] = strip_copy(spec['extras'])
                    else:
                        del spec['extras']

                to_update[package] = strip_copy(spec)

            section.update(to_update)

    with open(path, 'w') as f:
        f.write(dumps(data))


class ApiComponent(BaseComponent):
    def __init__(self, black_mode: Mode, isort_config: Config):
        self.black_mode = black_mode
        self.isort_config = isort_config

    def accept(self, path: Path, context: Mapping):
        try:
            sub_path = path.relative_to('api/src/___project_name__snake___')
        except ValueError:
            sub_path = None

        if any([
            not context["api"]["enable"],
            Path("api") not in path.parents,
            any(x.name == '.idea' for x in path.parents),
            sub_path == Path("people/migrations/0001_initial.py"),
            path.name.endswith(".pyc"),
            path == Path('api/poetry.lock'),
        ]):
            return False

        if not context['api']['channels']:
            if any([
                sub_path == Path("django/routing.py"),
                sub_path == Path("django/asgi.py"),
            ]):
                return False

        if not context['api']['celery']:
            if sub_path == Path("django/celery.py"):
                return False

        return True

    def post_process(self, root: Path, path: Path, context: Mapping) -> None:
        if path == Path("api/manage.py") or path == Path("api/pmanage"):
            (root / path).chmod(0o755)

        if path.name.endswith(".py"):
            format_file_in_place(src=root / path, mode=self.black_mode, fast=False)
            sort_imports(file_name=f"{root / path}", config=self.isort_config)

        if path == Path('api/pyproject.toml'):
            clean_pyproject(root / path)
