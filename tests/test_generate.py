"""
Generates a project for every combination of options and checks that the
result is complete and clean.

The fast tier (default) only generates the projects and checks them
statically. The slow tier (``pytest -m slow``) also installs the generated
front-ends and runs their own linters, type checks and tests, then starts the
projects like a developer would. It requires network access, ``pnpm``,
``poetry`` and Java (the TypeScript client generation). Starting projects with
an API also needs PostgreSQL and Redis: set ``PM_TEST_DATABASE_URL`` to a
server URL (like ``postgresql://postgres:postgres@localhost:5432/postgres``)
with the right to create databases, and run Redis on localhost.
"""

import contextlib
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pathspec
import pytest
import yaml

from model_w.project_maker.__main__ import build_context, build_maker
from model_w.project_maker.maker._base import LOCAL_FILES
from model_w.project_maker.namer import generate_declinations
from model_w.project_maker.template import INLINE_REF
from model_w.project_maker.wizard.preview import planned_files, template_files

TEMPLATE = (
    Path(__file__).parent.parent / "src" / "model_w" / "project_maker" / "template"
)
PROJECT_NAME = "Demo Thing"
ADMIN_PREFIX = "quiet-otter"


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
        admin_prefix=ADMIN_PREFIX,
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
        p.relative_to(root).as_posix()
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

    # Without the local clutter (dependencies, build outputs...)
    for rel in template_files():
        path = TEMPLATE / rel
        sources = [f"{rel}"]

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
            assert f"/back/{ADMIN_PREFIX}/cms/login/" in config
        elif combo.api:
            assert f"/back/{ADMIN_PREFIX}/admin/login/" in config
        else:
            assert "/login/?next=" in config
            assert "/back/" not in config


def test_snow_matches_options(project):
    """
    The deployment only declares the components and resources the options
    need, and gives each component the variables it expects.
    """

    combo, root = project
    snow = yaml.safe_load((root / "snow.yml").read_text())
    wagtail = combo.api and combo.wagtail
    redis = wagtail or (combo.api and combo.channels)

    images = {i["id"] for i in snow["images"]}
    components = {c["id"] for c in snow["components"]}
    ingresses = {
        i["match"]["prefix"]: i["target"]["component"] for i in snow["ingresses"]
    }
    resources = snow.get("resources") or {}
    envs = snow["envs"]

    api = {"api", "api-migrate", "api-worker"} if combo.api else set()
    front = {"front"} if combo.front else set()
    assert images == {"api"} & api | front
    assert components == api | front

    if combo.front and combo.api:
        assert ingresses == {"/back": "api", "/": "front"}
    else:
        assert ingresses == {"/": "api" if combo.api else "front"}

    assert ("redis_clusters" in resources) is redis
    assert ("pg_databases" in resources) is combo.api

    if combo.api:
        assert ("REDIS_URL" in envs["django"]) is redis
        assert ("AWS_STORAGE_BUCKET_NAME" in envs["django"]) is wagtail

    if combo.front:
        # Same variables as the ones validated in src/env.ts
        expected = {"SENTRY_DSN", "SENTRY_ENVIRONMENT"} | (
            {"API_URL"} if combo.api else set()
        )
        assert set(envs["front"]) == expected
        env_ts = (root / "front" / "src" / "env.ts").read_text()
        assert all(f"{name}:" in env_ts for name in expected)


def test_api_runs_in_debug_locally(project):
    """
    The local .env (created from .env-template) enables the debug mode, which
    the development needs (debug toolbar, API docs, TS client generation).
    """

    combo, root = project

    if not combo.api:
        pytest.skip("No API")

    lines = (root / "api" / ".env").read_text(encoding="utf-8").splitlines()

    assert "DEBUG=yes" in lines


def test_components_stay_in_their_folder(project):
    """
    Each component only brings files from its own folder: no api/ without
    API, no front/ without front-end.
    """

    combo, root = project
    top = {Path(f).parts[0] for f in rel_files(root)}

    assert ("api" in top) is combo.api
    assert ("front" in top) is combo.front


def test_wizard_preview_matches_generation(project):
    """
    The wizard previews the files of the project with the generation's rules,
    so it must list exactly the files that get generated.
    """

    combo, root = project
    planned = {f"{p}" for p in planned_files(make_context(combo), lock=False)}

    assert planned == rel_files(root)


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


def resolve(cmd: list[str]) -> list[str]:
    """On Windows, the .cmd shims (like pnpm's) must be resolved explicitly"""

    return [shutil.which(cmd[0]) or cmd[0], *cmd[1:]]


def poetry_env() -> dict[str, str]:
    """Poetry must use the generated project's venv, not the one of the tests"""

    return {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        resolve(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
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


@contextmanager
def serve(cmd: list[str], cwd: Path, log: Path, env: dict[str, str] | None = None):
    """
    Runs a server in the background for the duration of the block, then
    kills it with all its children (pnpm starts node, poetry starts python).
    """

    with open(log, "w", encoding="utf-8") as out:
        if os.name == "nt":
            flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            flags = {"start_new_session": True}

        proc = subprocess.Popen(
            resolve(cmd),
            cwd=cwd,
            env=env,
            stdout=out,
            stderr=subprocess.STDOUT,
            **flags,
        )

        try:
            yield proc
        finally:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", f"{proc.pid}"],
                    capture_output=True,
                )
            else:
                # Already gone if it crashed
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGTERM)

            proc.wait(timeout=30)


def wait_for_page(url: str, proc: subprocess.Popen, log: Path, timeout=180) -> str:
    """Waits until the URL answers a 200, then returns the page"""

    deadline = time.monotonic() + timeout
    last = ""

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            pytest.fail(f"The server stopped:\n{log.read_text(encoding='utf-8')}")

        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
        except OSError as e:
            last = f"{e}"

        time.sleep(1)

    pytest.fail(f"{url} never answered ({last}):\n{log.read_text(encoding='utf-8')}")


def prepare_api(api: Path, combo: Combo, server_url: str) -> None:
    """
    What a developer does before starting the API: install it, create its
    database and fill the .env (database, and a media bucket for Wagtail,
    which isn't used to show the admin), then migrate.
    """

    env = poetry_env()
    database = f"pm_start_{combo.id.replace('-', '_')}"
    url = urlsplit(server_url)

    run(["poetry", "install", "--no-interaction"], api, env)
    run(
        [
            "poetry",
            "run",
            "python",
            "-c",
            "import sys, psycopg\n"
            "with psycopg.connect(sys.argv[1], autocommit=True) as c:\n"
            "    c.execute(f'DROP DATABASE IF EXISTS {sys.argv[2]}')\n"
            "    c.execute(f'CREATE DATABASE {sys.argv[2]}')",
            server_url,
            database,
        ],
        api,
        env,
    )

    dotenv = api / ".env"
    lines = [
        line
        for line in dotenv.read_text(encoding="utf-8").splitlines()
        if not line.startswith("DATABASE_URL=")
    ]
    lines.append(f"DATABASE_URL={urlunsplit(url._replace(path=f'/{database}'))}")

    if combo.wagtail:
        lines += [
            "AWS_ACCESS_KEY_ID=x",
            "AWS_SECRET_ACCESS_KEY=x",
            "AWS_STORAGE_BUCKET_NAME=x",
            "AWS_S3_CUSTOM_DOMAIN=localhost/x",
        ]

    dotenv.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    try:
        run(["poetry", "run", "python", "manage.py", "migrate", "--noinput"], api, env)
    except AssertionError as e:
        # Which .env the API really loads, from within manage.py's process
        # (the .env is found from the call stack)
        script = (
            "import os, runpy, sys\n"
            "import model_w.env_manager._dotenv as d\n"
            "original = d.find_dotenv\n"
            "def find(*args, **kwargs):\n"
            "    found = original(*args, **kwargs)\n"
            "    print('find_dotenv:', found, 'prefix:', sys.prefix)\n"
            "    return found\n"
            "d.find_dotenv = find\n"
            "sys.argv = ['manage.py', 'shell', '-c', 'import os; "
            "from django.conf import settings; "
            'print("URL:", (os.environ.get("DATABASE_URL") or "").split("@")[-1]); '
            'print("ENGINE:", settings.DATABASES.get("default", {}).get("ENGINE"))\']\n'
            "runpy.run_path('manage.py', run_name='__main__')\n"
        )
        diagnostic = subprocess.run(
            resolve(["poetry", "run", "python", "-c", script]),
            cwd=api,
            env=env,
            capture_output=True,
            text=True,
        )
        written = [line.split("@")[-1] for line in lines if "DATABASE_URL" in line]
        pytest.fail(
            f"{e}\n\nDiagnostic:\n{diagnostic.stdout}{diagnostic.stderr}"
            f"Written: {written}"
        )


@pytest.mark.slow
def test_project_starts(locked_project, tmp_path):
    """
    Starts the project in development like a developer would (the API's
    runserver, the front's dev server), with the generated configuration:
    the front serves its pages, and the API's admin answers both directly and
    through the front's proxy (single origin).
    """

    combo, root = locked_project
    server_url = os.environ.get("PM_TEST_DATABASE_URL")

    if combo.api and not server_url:
        pytest.skip("Starting the API needs PM_TEST_DATABASE_URL (see above)")

    with contextlib.ExitStack() as stack:
        if combo.api:
            api = root / "api"
            prepare_api(api, combo, server_url)
            log = tmp_path / "api.log"
            proc = stack.enter_context(
                serve(
                    [
                        "poetry",
                        "run",
                        "python",
                        "manage.py",
                        "runserver",
                        "127.0.0.1:8000",
                        "--noreload",
                    ],
                    api,
                    log,
                    poetry_env(),
                )
            )
            admin = f"/back/{ADMIN_PREFIX}/admin/login/"

            assert "Django" in wait_for_page(f"http://127.0.0.1:8000{admin}", proc, log)

            if combo.wagtail:
                cms = f"http://127.0.0.1:8000/back/{ADMIN_PREFIX}/cms/login/"
                assert "Wagtail" in wait_for_page(cms, proc, log)

        if combo.front:
            front = root / "front"
            run(["pnpm", "install", "--frozen-lockfile", "--prefer-offline"], front)
            log = tmp_path / "front.log"
            proc = stack.enter_context(serve(["pnpm", "dev"], front, log))
            page = "/non-cms" if combo.wagtail else "/"
            html = wait_for_page(f"http://127.0.0.1:3000{page}", proc, log)

            assert PROJECT_NAME in html

            if combo.api:
                proxied = wait_for_page(f"http://127.0.0.1:3000{admin}", proc, log)
                assert "Django" in proxied
