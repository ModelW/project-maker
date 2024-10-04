"""Fixtures related to the front end we're testing on."""

import fcntl
import os
import select
import subprocess
import time
from collections.abc import Generator
from logging import getLogger
from pathlib import Path

import pytest
from django.conf import settings
from playwright.sync_api import ConsoleMessage, Page, Request
from pytest_django.fixtures import SettingsWrapper
from pytest_django.live_server_helper import LiveServer

from . import utils

logger = getLogger(__name__)


@pytest.fixture(autouse=True)
def overwrite_settings(settings: SettingsWrapper, front_server: str) -> SettingsWrapper:
    """
    Overwrite any settings at runtime just for testing.

    ie. dynamic base URL, file storage, etc.
    """
    base_url = front_server.strip("/")
    settings.BASE_URL = base_url

    # We use InMemoryStorage for local testing, and a Dockerised S3, for CI/CD testing
    in_memory_file_storage = "django.core.files.storage.InMemoryStorage"
    boto3_file_storage = "storages.backends.s3boto3.S3Boto3Storage"
    default_file_storage = os.environ.get(
        "DEFAULT_FILE_STORAGE",
        in_memory_file_storage,
    )

    if default_file_storage == boto3_file_storage:
        settings.AWS_S3_ENDPOINT_URL = settings.AWS_S3_CUSTOM_DOMAIN
        settings.AWS_S3_URL_PROTOCOL = settings.AWS_S3_ENDPOINT_URL.split("//", 1)[0]

    settings.DEFAULT_FILE_STORAGE = default_file_storage

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


@pytest.fixture(scope="session")
def front_dir() -> Path | None:
    """
    Location of the front-end source code.
    Note: If the environment variable FRONTURL is set, this fixture will return None.
    """
    directory = None
    if not os.environ.get("FRONTURL"):
        directory = settings.BASE_DIR / ".." / "front"
    return directory


@pytest.fixture(scope="session")
def vite_path(front_dir: Path | None) -> Path:
    """
    Location of the vite binary.

    Unlike Nuxt, we can't specify a port to run on with `npm run preview`,
    so instead we run the vite binary directly with the port we want.
    """
    path = None
    if not os.environ.get("FRONTURL"):
        path = front_dir / "node_modules/.bin/vite"
    return path


@pytest.fixture(scope="session")
def front_env(live_server: LiveServer):
    """Environment variables to be injected into the front."""
    return {
        "PUBLIC_API_URL": live_server.url,
        "VITE_API_URL": live_server.url,
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
        logger.info("Running npm run build")
        subprocess.run(
            ["npm", "run", "build"],
            cwd=front_dir,
            check=True,
            env={**os.environ, **front_env},
        )
        did_build = True
    else:
        logger.info("Not running npm run build")

    return did_build


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
          environment variable FRONTURL.
    """
    if server_address := os.environ.get("FRONTURL"):
        logger.info(f"Using FRONTURL env var: {server_address} as front server.")
        yield server_address

    else:
        with subprocess.Popen(
            [vite_path, "preview", "--port", "0"],
            cwd=front_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            env={**os.environ, **front_env},
        ) as p:
            logger.info("Starting the front-end server...")
            for stream in [p.stdout, p.stderr]:
                fd = stream.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            server_address = None
            total_timeout = 10
            start_time = time.time()
            output = {"stdout": "", "stderr": ""}

            try:
                while not server_address:
                    remaining_time = total_timeout - (time.time() - start_time)

                    if remaining_time <= 0:
                        raise TimeoutError(
                            f"Server did not start within the given timeout. "
                            f"Stdout: {output['stdout']} Stderr: {output['stderr']}",
                        )

                    ready, _, _ = select.select(
                        [p.stdout, p.stderr],
                        [],
                        [],
                        remaining_time,
                    )

                    for stream in ready:
                        try:
                            line = stream.readline()
                            if stream is p.stdout:
                                output["stdout"] += line
                            else:
                                output["stderr"] += line
                        except OSError:
                            continue

                        if stream is p.stdout and line:
                            if match := utils.get_svelte_1_server_url(line):
                                server_address = match
                                break
                        elif not line:
                            break

                server_address = utils.strip_ansi(server_address)

                # We force localhost rather than IP, so the cookies work
                if "127.0.0.1" in server_address:
                    server_address = server_address.replace("127.0.0.1", "localhost")

                yield server_address

            except Exception as e:
                raise ChildProcessError(
                    f"Failed to start the server: {e!s} "
                    f"Stdout: {output['stdout']} Stderr: {output['stderr']}",
                )
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
