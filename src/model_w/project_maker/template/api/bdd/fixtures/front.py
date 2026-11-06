"""Fixtures related to the front end we're testing on."""

import fcntl
import os
import select
import subprocess
import time
from collections.abc import Generator
from logging import getLogger
from pathlib import Path

import httpx
import pytest
from django.conf import settings
from playwright.sync_api import ConsoleMessage, Page, Request
from pytest_django.fixtures import Settings
from pytest_django.live_server_helper import LiveServer

from . import utils

logger = getLogger(__name__)


@pytest.fixture(autouse=True)
def overwrite_storage_settings(
    settings: Settings, live_server: LiveServer, tmp_path: Path
):
    """
    Overwrite any storage settings at runtime just for testing.
    We use the local file system for local testing, and a dockerised minio S3 for
    CI/CD testing.
    """

    # We use FileSystemStorage (temp directory) for local testing, and a
    # Dockerised S3, for CI/CD testing
    local_file_storage = "django.core.files.storage.FileSystemStorage"
    boto3_file_storage = "storages.backends.s3boto3.S3Boto3Storage"
    default_file_storage = os.environ.get(
        "DEFAULT_FILE_STORAGE",
        local_file_storage,
    )

    if default_file_storage == boto3_file_storage:
        settings.AWS_S3_URL_PROTOCOL = "http:"
        settings.AWS_S3_ENDPOINT_URL = str(
            httpx.URL(
                f"{settings.AWS_S3_URL_PROTOCOL}//{settings.AWS_S3_CUSTOM_DOMAIN}",
            ).copy_with(path=""),
        )

    else:
        media_directory = tmp_path / "test_media"
        settings.MEDIA_ROOT = str(media_directory)
        settings.MEDIA_URL = live_server.url

    settings.STORAGES = {
        "default": {
            "BACKEND": default_file_storage,
        },
        "staticfiles": {
            # Non-manifest storage: the live test server serves static files via the
            # staticfiles finders, which can't resolve hashed names (only present in
            # STATIC_ROOT). Without this, assets like the Wagtail userbar 404.
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"
        },
    }

    # Don't use the cache for tests. Assign a new dict (rather than mutating in
    # place) so Django's `setting_changed` signal fires and the already-open
    # cache connection (e.g. Redis) is reset.
    settings.CACHES = {
        alias: {
            **config,
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
        for alias, config in settings.CACHES.items()
    }

    return settings


@pytest.fixture(autouse=True)
def overwrite_settings(
    overwrite_storage_settings: Settings,
    front_server: str,
) -> Settings:
    """
    Overwrite any settings at runtime just for testing.

    ie. dynamic base URL, file storage, etc.
    """
    base_url = front_server.strip("/")
    settings.BASE_URL = base_url
    # :: IF api__wagtail
    settings.WAGTAILADMIN_BASE_URL = settings.WAILER_BASE_URL = base_url
    # :: ENDIF
    base_origin = base_url.replace(":80", "").split("://", 1)[-1]
    settings.CSRF_TRUSTED_ORIGINS = [
        f"{scheme}://{base_origin}" for scheme in ["http", "https"]
    ]
    return settings


@pytest.fixture(autouse=True)
def console(page: Page) -> list[ConsoleMessage]:
    """
    Capture the messages from the browser console and returns them as a list.

    To use, simply add `console` as an argument to your test function
    Example:
    ```
    def test_something(console):
        assert any("Hello world!" in msg.text for msg in console)
        assert any("error" == msg.type for msg in console)
    ```
    """
    logs: list[ConsoleMessage] = []

    def capture_log(msg: ConsoleMessage) -> None:
        logs.append(msg)

    page.on("console", capture_log)

    return logs


@pytest.fixture(autouse=True)
def network_requests(page: Page) -> list[Request]:
    """
    Capture the network requests made by the browser and returns them in a list.

    To use, simply add `network_requests` as an argument to your test function
    Example:
    ```
    def test_something(network_requests):
        assert any("example.com" in request.url for request in network_requests)
    ```
    """
    requests: list[Request] = []

    def capture_request(request: Request) -> None:
        requests.append(request)

    page.on("request", capture_request)

    return requests


# :: IFNOT front__enable
# Defined before the front-end fixtures on purpose: in the raw template, where
# both exist, the front-end version below overrides this one.
@pytest.fixture(scope="session")
def front_server(live_server: LiveServer) -> str:
    """
    There is no front-end in this project. The site is reached through the
    router if `BDD_FRONT_URL` points to it (as in Docker), otherwise through
    the API's live server directly.
    """
    if server_address := os.environ.get("BDD_FRONT_URL"):
        utils.wait_for_url(server_address)
        return server_address

    return live_server.url


# :: ENDIF
# :: IF front__enable
@pytest.fixture(scope="session")
def front_dir() -> Path | None:
    """
    Location of the front-end source code.
    Note: If the environment variable BDD_FRONT_URL is set (to use an already
          running front), this fixture will return None.
    """
    directory = None
    if not os.environ.get("BDD_FRONT_URL"):
        directory = settings.BASE_DIR / ".." / "front"
    return directory


@pytest.fixture(scope="session")
def vite_path(front_dir: Path | None) -> Path:
    """
    Location of the vite binary.

    Unlike Nuxt, we can't specify a port to run on with `pnpm run preview`,
    so instead we run the vite binary directly with the port we want.
    """
    path = None
    if not os.environ.get("BDD_FRONT_URL"):
        path = front_dir / "node_modules/.bin/vite"
    return path


@pytest.fixture(scope="session")
def front_env(live_server: LiveServer):
    """
    Environment variables to be injected into the front (merged over the current
    environment). The Sentry ones are required by the front, but may be empty.
    """
    return {
        "API_URL": live_server.url,
        "SENTRY_DSN": "",
        "SENTRY_ENVIRONMENT": "test",
    }


@pytest.fixture(scope="session")
def front_build(front_dir: Path, vite_path: Path, front_env: dict) -> bool:
    """
    Build the front-end.

    Note: As sometimes you want a test to run quickly without the build
          rather long stage, you can set the environment variable SKIPBUILD=1
    """
    did_build = False

    if os.environ.get("SKIPBUILD", "0") != "1":
        logger.info("Running pnpm run build")
        subprocess.run(
            # pnpm is looked up in the PATH on purpose, as its install location
            # depends on each developer's (or CI's) setup.
            ["pnpm", "run", "build"],  # noqa: S607
            cwd=front_dir,
            check=True,
            env={**os.environ, **front_env},
        )
        did_build = True
    else:
        logger.info("Not running pnpm run build")

    return did_build


def _set_non_blocking(process: subprocess.Popen) -> None:
    """
    Make the stdout and stderr of the process non-blocking, so that we can
    read them without hanging.

    Parameters
    ----------
    process
        The process whose output streams must be made non-blocking
    """
    for stream in [process.stdout, process.stderr]:
        fd = stream.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


def _wait_for_server_address(
    process: subprocess.Popen,
    output: dict[str, str],
    total_timeout: float,
) -> str:
    """
    Read the output of the front-end server until it prints its URL.

    Parameters
    ----------
    process
        The running front-end server
    output
        Accumulates what the server printed so far, in its "stdout" and
        "stderr" keys
    total_timeout
        Maximum time (in seconds) to wait for the server to start
    """
    server_address = None
    start_time = time.time()

    while not server_address:
        remaining_time = total_timeout - (time.time() - start_time)

        if remaining_time <= 0:
            msg = (
                f"Server did not start within the given timeout. "
                f"Stdout: {output['stdout']} Stderr: {output['stderr']}"
            )
            raise TimeoutError(msg)

        ready, _, _ = select.select(
            [process.stdout, process.stderr],
            [],
            [],
            remaining_time,
        )

        for stream in ready:
            try:
                line = stream.readline()
                if stream is process.stdout:
                    output["stdout"] += line
                else:
                    output["stderr"] += line
            except OSError:
                continue

            if stream is process.stdout and line:
                if match := utils.get_svelte_1_server_url(line):
                    server_address = match
                    break
            elif not line:
                break

    return server_address


@pytest.fixture(scope="session")
def front_server(
    front_build: bool,
    front_dir: Path | None,
    vite_path: Path,
    front_env: dict,
) -> Generator[str, None, None]:
    """
    Start the front-end until all tests are done.
    The returned value is the base URL of that running front-end.

    Note: To test on a URL without starting the server, you can set the
          environment variable BDD_FRONT_URL.
    """
    if server_address := os.environ.get("BDD_FRONT_URL"):
        logger.info("Using BDD_FRONT_URL env var: %s as front server.", server_address)
        utils.wait_for_url(server_address)
        yield server_address

    else:
        # The command is built from the front directory, not from user input
        with subprocess.Popen(  # noqa: S603
            [vite_path, "preview", "--port", "0"],
            cwd=front_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            env={**os.environ, **front_env},
        ) as p:
            logger.info("Starting the front-end server...")
            _set_non_blocking(p)

            output = {"stdout": "", "stderr": ""}

            try:
                server_address = _wait_for_server_address(
                    p,
                    output,
                    total_timeout=10,
                )
                server_address = utils.strip_ansi(server_address)

                # We force localhost rather than IP, so the cookies work
                if "127.0.0.1" in server_address:
                    server_address = server_address.replace("127.0.0.1", "localhost")

                yield server_address

            except Exception as e:
                msg = (
                    f"Failed to start the server: {e!s} "
                    f"Stdout: {output['stdout']} Stderr: {output['stderr']}"
                )
                raise ChildProcessError(msg) from e
            finally:
                # Capture and log any remaining output
                remaining_output = "".join(p.stdout.readlines())
                remaining_error = "".join(p.stderr.readlines())

                if remaining_output:
                    logger.info("Front-end server logs:\n%s", remaining_output.strip())
                if remaining_error:
                    logger.error(
                        "Front-end server error logs:\n%s",
                        remaining_error.strip(),
                    )

                p.terminate()


# :: ENDIF
