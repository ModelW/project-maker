"""
Generates a project for every combination of options and checks that the
result is complete and clean.

The fast tier (default) only generates the projects and checks them
statically. The slow tier (``pytest -m slow``) also installs the generated
front-ends and runs their own linters, type checks and tests, which requires
network access, ``pnpm`` and ``poetry``.
"""

import re
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pathspec
import pytest

from model_w.project_maker.__main__ import build_context, build_maker
from model_w.project_maker.maker._base import LOCAL_FILES
from model_w.project_maker.namer import generate_declinations
from model_w.project_maker.template import INLINE_REF

TEMPLATE = (
    Path(__file__).parent.parent / "src" / "model_w" / "project_maker" / "template"
)
PROJECT_NAME = "Demo Thing"
CMS_PREFIX = "cms-admin"


@dataclass(frozen=True)
class Combo:
    """A combination of the options of the wizard"""

    front: bool
    api: bool
    wagtail: bool = False
    channels: bool = False
    demo_snippet: bool = False

    @property
    def id(self) -> str:
        flags = dict(
            front=self.front,
            api=self.api,
            wagtail=self.wagtail,
            channels=self.channels,
            snippet=self.demo_snippet,
        )
        return "-".join(k for k, v in flags.items() if v)


def _combos() -> list[Combo]:
    out = [Combo(front=True, api=False)]

    for front in (True, False):
        for channels in (False, True):
            out.append(Combo(front=front, api=True, channels=channels))

            for demo_snippet in (False, True):
                out.append(
                    Combo(
                        front=front,
                        api=True,
                        wagtail=True,
                        channels=channels,
                        demo_snippet=demo_snippet,
                    )
                )

    return out


COMBOS = _combos()

#: Combinations installed and linted by the slow tier: each option is covered
#: at least once in both states without paying for the full matrix
SLOW_COMBOS = [
    Combo(front=True, api=False),
    Combo(front=True, api=True),
    Combo(front=True, api=True, wagtail=True, channels=True, demo_snippet=True),
]


def make_context(combo: Combo) -> dict:
    """Builds the generation context the same way the wizard does"""

    return build_context(
        project_name={"initial": PROJECT_NAME, **generate_declinations(PROJECT_NAME)},
        front=combo.front,
        api=combo.api,
        wagtail=combo.wagtail,
        channels=combo.channels,
        demo_snippet=combo.demo_snippet,
        cms_prefix=CMS_PREFIX,
        dev_id="Dev <dev@example.com>",
        secret_key="not-secret",
    )


def generate(combo: Combo, target: Path, lock: bool) -> Path:
    """Generates the project into target and returns its path"""

    build_maker(lock=lock).make(TEMPLATE, target, make_context(combo))
    return target


@pytest.fixture(scope="session", autouse=True)
def git_identity() -> Iterator[None]:
    """The generator commits into the new repository, which needs an identity"""

    with pytest.MonkeyPatch.context() as mp:
        for prefix in ("GIT_AUTHOR", "GIT_COMMITTER"):
            mp.setenv(f"{prefix}_NAME", "Test")
            mp.setenv(f"{prefix}_EMAIL", "test@example.com")
        yield


@pytest.fixture(scope="module", params=COMBOS, ids=lambda c: c.id)
def project(request, tmp_path_factory) -> tuple[Combo, Path]:
    combo: Combo = request.param
    target = tmp_path_factory.mktemp("gen") / "demo-thing"
    return combo, generate(combo, target, lock=False)


def text_files(root: Path) -> Iterator[Path]:
    """All the UTF-8 files of a tree, outside of .git"""

    for path in root.rglob("*"):
        if ".git" in path.relative_to(root).parts or not path.is_file():
            continue

        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        yield path


def rel_files(root: Path) -> set[str]:
    return {
        f"{p.relative_to(root)}"
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def test_template_references_are_known():
    """
    A reference to an unknown key silently renders as an empty string, which
    is how `___snippet_preview___` once became `/`. Make sure every reference
    in the template points to something the context provides.
    """

    context = make_context(
        Combo(front=True, api=True, wagtail=True, channels=True, demo_snippet=True)
    )
    unknown = set()
    skipped = {
        "node_modules",
        ".svelte-kit",
        "__pycache__",
        ".venv",
        ".idea",
        "results",
    }

    for path in TEMPLATE.rglob("*"):
        rel = path.relative_to(TEMPLATE)

        if skipped & set(rel.parts):
            continue

        sources = [f"{rel}"]

        if path.is_file():
            try:
                sources.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                pass

        for source in sources:
            for m in INLINE_REF.finditer(source):
                ref = m.group("ref1") or m.group("ref2")
                ptr = context

                for key in re.split(r"__|~~", ref):
                    ptr = ptr.get(key) if isinstance(ptr, dict) else None

                if ptr is None:
                    unknown.add((ref, f"{rel}"))

    assert not unknown, sorted(unknown)


def test_no_template_leftovers(project):
    _, root = project
    leftovers = []

    for path in text_files(root):
        if path.name == "pnpm-lock.yaml":
            continue

        content = path.read_text(encoding="utf-8")

        for i, line in enumerate(content.splitlines(), start=1):
            if re.match(r"^\s*(#|//) ::", line):
                leftovers.append(f"{path.relative_to(root)}:{i}: {line.strip()}")

        for m in INLINE_REF.finditer(content):
            leftovers.append(f"{path.relative_to(root)}: {m.group(0)}")

    assert not leftovers


def test_front_is_svelte_5(project):
    combo, root = project

    if not combo.front:
        pytest.skip("No front")

    forbidden = re.compile(
        # Svelte 4 syntax, and legacy SvelteKit modules (`$app/env` is fine:
        # it's SvelteKit 3's replacement of `$app/environment`)
        r"export let |<slot[\s/>]|<svelte:component"
        r"|\$app/environment|\$app/stores|\$env/"
    )
    offenders = [
        f"{p.relative_to(root)}: {m.group(0)}"
        for p in (root / "front" / "src").rglob("*")
        if p.suffix in {".svelte", ".ts"}
        for m in forbidden.finditer(p.read_text(encoding="utf-8"))
    ]

    assert not offenders


def test_expected_files(project):
    combo, root = project
    files = rel_files(root)
    wagtail = combo.api and combo.wagtail
    snake = "demo_thing"

    def present(path: str, expected: bool):
        assert (path in files) is expected, (
            f"{path} should {'' if expected else 'not '}exist"
        )

    present(".github/workflows/ci.yml", True)
    present(".github/workflows/e2e.yml", combo.api)
    present("api/bdd/_infrastructure/mock-digital-ocean-router.conf", combo.api)
    present("front/package.json", combo.front)
    present("front/pnpm-lock.yaml", combo.front)
    present("api/pyproject.toml", combo.api)
    present(f"api/{snake}/django/asgi.py", combo.channels)
    present(f"api/{snake}/apps/cms/snippets.py", combo.demo_snippet)
    present(f"api/{snake}/apps/cms/migrations/0003_demosnippet.py", combo.demo_snippet)

    if combo.front:
        present("front/src/lib/session/provider.ts", True)
        present("front/src/lib/session/provider.no-api.ts", False)
        present("front/src/lib/session/types.no-api.ts", False)
        present("front/src/lib/api/client/apis/MeApi.ts", combo.api)
        present(
            f"api/{snake}/apps/people/management/commands/generate_ts_client.py",
            combo.api and combo.front,
        )
        present("front/src/lib/meta-router/config.ts", True)
        present("front/src/routes/(site)/+page.svelte", not wagtail)
        present("front/src/routes/(site)/non-cms/+page.svelte", wagtail)
        present("front/src/routes/(preview)/__block_preview__/+page.ts", wagtail)
        present("front/src/routes/(preview)/__snippet_preview__/+page.ts", wagtail)
        present("front/src/params/cmsPath.ts", wagtail)
        present("front/src/lib/components/cms/StreamField.svelte", wagtail)
        present(
            "front/src/lib/components/cms/snippets/DemoSnippet.svelte",
            combo.demo_snippet,
        )

        for demo in ["DemoBlock", "DemoSubBlock", "Heading"]:
            present(f"front/src/lib/components/cms/blocks/{demo}.svelte", False)

        provider = (root / "front/src/lib/session/provider.ts").read_text()
        # With an API, the session only goes through the generated client
        assert ("createApiClient" in provider) is combo.api

        config = (root / "front/src/lib/meta-router/config.ts").read_text()

        if wagtail:
            assert f"/back/{CMS_PREFIX}/login/" in config
        elif combo.api:
            assert "/back/admin/login/" in config
        else:
            assert "/login/?next=" in config
            assert "/back/" not in config


def test_no_local_files(project):
    """
    Files that only exist locally in the template (caches, dependencies,
    secrets, build outputs) must never reach a generated project.
    """

    _, root = project
    spec = pathspec.GitIgnoreSpec.from_lines(LOCAL_FILES)
    # Created on purpose from .env-template, for the developer to fill
    expected = {"api/.env", "front/.env"}
    leaked = sorted(
        f for f in rel_files(root) if spec.match_file(f) and f not in expected
    )

    assert not leaked


def test_api_is_lint_clean(project):
    combo, root = project

    if not combo.api:
        pytest.skip("No API")

    api = root / "api"

    for cmd in (["check", "."], ["format", "--check", "."]):
        result = subprocess.run(
            [sys.executable, "-m", "ruff", *cmd],
            cwd=api,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture(scope="module", params=SLOW_COMBOS, ids=lambda c: c.id)
def locked_project(request, tmp_path_factory) -> tuple[Combo, Path]:
    combo: Combo = request.param
    target = tmp_path_factory.mktemp("gen-slow") / "demo-thing"
    return combo, generate(combo, target, lock=True)


def run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, f"{cmd} failed:\n{result.stdout}\n{result.stderr}"


@pytest.mark.slow
def test_front_passes_its_own_checks(locked_project):
    combo, root = locked_project

    if not combo.front:
        pytest.skip("No front")

    front = root / "front"

    run(["pnpm", "install", "--frozen-lockfile", "--prefer-offline"], front)
    run(["pnpm", "lint"], front)
    run(["pnpm", "check"], front)
    run(["pnpm", "test", "--run"], front)
    run(["pnpm", "build"], front)


@pytest.mark.slow
def test_api_lock_is_consistent(locked_project):
    combo, root = locked_project

    if not combo.api:
        pytest.skip("No API")

    run(["poetry", "check", "--lock"], root / "api")
