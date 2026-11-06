#!/usr/bin/env python3
import shutil
import subprocess
from argparse import ArgumentParser
from collections.abc import Sequence
from os import getenv
from pathlib import Path
from signal import SIGTERM, signal
from sys import stderr
from typing import NamedTuple

from rich import print as rich_print

from .errors import ProjectMakerError
from .generate import build_context, build_maker, generate_random_key
from .wizard import WizardApp

__all__ = ["build_context", "build_maker", "generate_random_key", "main"]


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
    Executes a command and returns its output (empty if it failed)
    """

    return subprocess.run(
        args,
        capture_output=True,
        check=False,
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


def main(argv: Sequence[str] | None = None):
    check_binaries()
    args = parse_args(argv)
    outcome = WizardApp(
        dev_dir=Path(args.dev_dir),
        dev_id=get_developer_identity(),
    ).run()

    if outcome is None:
        rich_print("[red bold]ok, bye")
        exit(1)

    if not outcome.success:
        rich_print(f"[red][bold]Something went wrong[/bold]:\n{outcome.error}")
        exit(1)

    rich_print(
        f"[green bold]All clean and tidy, you can code![/green bold]\n"
        f"Your project is in [bold]{outcome.target}"
    )


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
