#!/usr/bin/env python3
import shlex
import shutil
import string
import subprocess
from argparse import ArgumentParser
from dataclasses import dataclass
from os import getenv
from pathlib import Path
from queue import Queue
from random import SystemRandom
from signal import SIGTERM, signal
from sys import stderr
from threading import Thread
from time import sleep
from typing import NamedTuple, Optional, Sequence

from black import Mode, TargetVersion
from isort import Config
from rich import print as rich_print
from rich.prompt import Confirm, Prompt

from .errors import ProjectMakerError
from .maker import ApiComponent, CommonComponent, FrontComponent, Maker
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

    binaries = {"npm", "node", "git", "git-flow"}
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


def parse_args(argv: Optional[Sequence[str]] = None) -> Args:
    dev_dir = Path(getenv("MODEL_W_DEV_DIR", Path.home() / "dev"))

    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dev-dir",
        help=f"Development directory that contains all projects (default: {dev_dir}, you can also set it with MODEL_W_DEV_DIR)",
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


def main(argv: Optional[Sequence[str]] = None):
    check_binaries()
    args = parse_args(argv)

    rich_print("[white bold on blue]\n  === Model W Project Maker ===  \n")

    rich_print(
        f"[gold3]Your dev dir is [bold]{args.dev_dir}[/bold]. You can change "
        f"it with the [bold]MODEL_W_DEV_DIR[/bold] environment variable.\n"
    )

    key = generate_random_key()

    context = dict(
        secret_key=shlex.quote(f"{key[:25]}wesh{key[25:]}"),
        front={},
        api={},
        project_name={},
        dev_id=get_developer_identity(),
    )

    accept_name = False

    while not accept_name:
        context["project_name"]["initial"] = Prompt.ask(
            "What is your project's (readable) name?"
        )
        context["project_name"].update(
            generate_declinations(context["project_name"]["initial"])
        )

        rich_print("[green]Got that, let's confirm:")

        for key in ["natural", "snake", "camel_up"]:
            rich_print(
                f'  [bold]->[/bold] [bold cyan]{key}[/bold cyan]: {context["project_name"][key]}'
            )

        accept_name = Confirm.ask("Fine for you?", default=True)
        print()

    context["project_title"] = context["project_name"]["natural"]

    context["front"]["enable"] = Confirm.ask("Will you have a front-end?", default=True)
    context["api"]["enable"] = Confirm.ask("Will you have a back-end?", default=True)

    if context["api"]["enable"]:
        context["api"]["wagtail"] = Confirm.ask("Would you like a Wagtail CMS?")
        context["api"]["celery"] = Confirm.ask("Do you expect using Celery queue?")
        context["api"]["channels"] = Confirm.ask(
            "Are you fancy enough to use WebSockets?"
        )
        context["api"]["wsgi"] = not context["api"]["channels"]
        context["api"]["redis"] = context["api"]["celery"] or context["api"]["channels"]

    if context["api"]["wagtail"]:
        context["cms_prefix"] = Prompt.ask(
            "What is the URL prefix for the CMS admin?", default="wubba-lubba-dub-dub"
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
        labels=dict(wagtail="Wagtail", celery="Celery", channels="Channels"),
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

    maker = Maker(
        [
            ApiComponent(
                black_mode=Mode(target_versions={TargetVersion.PY310}),
                isort_config=Config(
                    profile="black",
                    quiet=True,
                    known_first_party=[
                        context["project_name"]["snake"],
                    ],
                    src_paths=[create_path / "api" / "src"],
                ),
            ),
            FrontComponent(),
            CommonComponent(),
        ]
    )

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
