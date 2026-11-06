#!/usr/bin/env python3
import shlex
import shutil
import string
import subprocess
from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from queue import Queue
from random import SystemRandom
from signal import SIGTERM, signal
from sys import stderr
from threading import Thread
from time import sleep
from typing import NamedTuple

from rich import print as rich_print
from rich.prompt import Confirm, Prompt

from .errors import ProjectMakerError
from .maker import (
    ApiComponent,
    CommonComponent,
    FrontComponent,
    Maker,
    PrettierComponent,
)
from .namer import generate_declinations


class Args(NamedTuple):
    dev_dir: Path


def sigterm_handler(_, __):
    raise SystemExit(1)


def check_binaries():
    """
    Checks that the required binaries are installed. Otherwise the process will
    fail down the stream and that'll be sad.
    """

    binaries = {"npm", "node", "git", "git-flow", "poetry"}
    missing = set()

    for binary in binaries:
        if not shutil.which(binary):
            missing.add(binary)

    if missing:
        rich_print(
            f"[red]Missing binaries: {', '.join(missing)}. Please make sure "
            f"to install them before running this script[/red]"
        )
        exit(1)


def exec_get_stdout(args):
    """
    Executes a command and returns its output
    """

    return subprocess.run(
        args,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()


def get_developer_identity() -> str:
    """
    Returns the developer's identity, which is the name and email address of the
    git user.
    """

    name = exec_get_stdout(["git", "config", "user.name"]) or "???"
    email = exec_get_stdout(["git", "config", "user.email"]) or "???@???.?"

    return f"{name} <{email}>"


def keys_text(choices, labels):
    out = []

    for key, choice in choices.items():
        if choice and key in labels:
            out.append(labels[key])

    out_str = ""

    for i, label in enumerate(out):
        if i == 0:
            out_str += f"[bold]{label}[/bold]"
        elif i == len(out) - 1:
            out_str += f" and [bold]{label}[/bold]"
        else:
            out_str += f", [bold]{label}[/bold]"

    return out_str


def parse_args(argv: Sequence[str] | None = None) -> Args:
    dev_dir = Path(getenv("MODEL_W_DEV_DIR", Path.home() / "dev"))

    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dev-dir",
        help=(
            f"Development directory that contains all projects (default: "
            f"{dev_dir}, you can also set it with MODEL_W_DEV_DIR)"
        ),
        default=dev_dir,
    )

    return Args(**parser.parse_args(argv).__dict__)


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
    cms_prefix: str | None = None,
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
    cms_prefix
        URL prefix of the CMS admin (required with Wagtail)
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

        if wagtail:
            context["cms_prefix"] = cms_prefix or "wubba-lubba-dub-dub"

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


def make(maker: Maker, create_path: Path, context):
    running = True
    queue = Queue()
    tick_counter = 0

    class Tick:
        """
        Used by the display thread to notify the main thread to re-draw a new moon
        """

    @dataclass
    class Done:
        """
        Sent when the venv creation is done (either successfully or as a failure).
        The builder is there to be able to run commands afterwards.
        """

        success: bool

    def tick():
        while running:
            queue.put(Tick())
            sleep(0.1)

    def install():
        try:
            maker.make(
                Path(__file__).parent / "template",
                create_path,
                context,
            )
        except Exception:
            queue.put(Done(False))
            raise
        else:
            queue.put(Done(True))

    def print_tick():
        nonlocal tick_counter
        moons = "🌑🌒🌓🌔🌕🌖🌗🌘"

        stderr.write(
            "".join(
                [
                    "\r",
                    moons[tick_counter % len(moons)],
                    " Working... ",
                ]
            )
        )

        tick_counter += 1

    Thread(target=tick).start()
    Thread(target=install).start()

    while running and (msg := queue.get()):
        if isinstance(msg, Tick):
            print_tick()
        elif isinstance(msg, Done) and msg.success:
            running = False
            stderr.write("\r")
            rich_print("[green bold]All clean and tidy, you can code!")
        elif isinstance(msg, Done) and not msg.success:
            running = False
            stderr.write("\rSorry, something went wrong\n")
            exit(1)


def main(argv: Sequence[str] | None = None):
    check_binaries()
    args = parse_args(argv)

    rich_print("[white bold on blue]\n  === Model W Project Maker ===  \n")

    rich_print(
        f"[gold3]Your dev dir is [bold]{args.dev_dir}[/bold]. You can change "
        f"it with the [bold]MODEL_W_DEV_DIR[/bold] environment variable.\n"
    )

    project_name: dict = {}
    accept_name = False

    while not accept_name:
        project_name["initial"] = Prompt.ask("What is your project's (readable) name?")
        project_name.update(generate_declinations(project_name["initial"]))

        rich_print("[green]Got that, let's confirm:")

        for key in ["natural", "snake", "camel_up"]:
            rich_print(
                f"  [bold]->[/bold] [bold cyan]{key}[/bold cyan]: {project_name[key]}"
            )

        accept_name = Confirm.ask("Fine for you?", default=True)
        print()

    front = Confirm.ask("Will you have a front-end?", default=True)
    api = Confirm.ask("Will you have a back-end?", default=True)
    wagtail = False
    channels = False
    demo_snippet = False
    cms_prefix = None

    if api:
        wagtail = Confirm.ask("Would you like a Wagtail CMS?")
        channels = Confirm.ask("Are you fancy enough to use WebSockets?")

        if wagtail:
            cms_prefix = Prompt.ask(
                "What is the URL prefix for the CMS admin?",
                default="wubba-lubba-dub-dub",
            )
            demo_snippet = Confirm.ask(
                "Add a demo snippet (shows how snippet previews work)?",
                default=False,
            )

    context = build_context(
        project_name=project_name,
        front=front,
        api=api,
        wagtail=wagtail,
        channels=channels,
        demo_snippet=demo_snippet,
        cms_prefix=cms_prefix,
        dev_id=get_developer_identity(),
    )

    components = keys_text(
        dict(front=context["front"]["enable"], api=context["api"]["enable"]),
        dict(front="a front-end", api="a back-end"),
    )

    if not components:
        rich_print("\nYou don't want [red bold]anything[/red bold]? Not fun")
        exit(1)

    extras = keys_text(
        context["api"],
        labels=dict(
            wagtail="Wagtail",
            channels="Channels",
            demo_snippet="a demo snippet",
        ),
    )

    if extras:
        extras = f" Also you want {extras} to go with it."

    rich_print(f"\nYou want {components}.{extras}\n")

    confirm = Confirm.ask("Is that right?", default=True)

    if not confirm:
        rich_print("\nIncapable of making a choice. Like always. I see.")
        exit(1)

    create_path = args.dev_dir / context["project_name"]["dashed"]

    rich_print(f"\n[blue]Creating in: [bold]{create_path}")

    confirm = Confirm.ask("Is that right?")

    if not confirm:
        rich_print("\nIncapable of taking a decision. Like always. I see.")
        exit(1)

    maker = build_maker()

    print()

    make(maker, create_path, context)


def __main__():
    signal(SIGTERM, sigterm_handler)

    try:
        main()
    except KeyboardInterrupt:
        rich_print("[red bold]ok, bye\n", file=stderr)
        exit(1)
    except ProjectMakerError as e:
        rich_print(f"[red][bold]Error[/bold]: {e}\n", file=stderr)
        exit(1)


if __name__ == "__main__":
    __main__()
