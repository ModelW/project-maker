#!/usr/bin/env python3
from argparse import ArgumentParser
from os import getenv
from pathlib import Path
from signal import SIGTERM, signal
from sys import stderr
from typing import NamedTuple, Optional, Sequence

from black import Mode, TargetVersion
from isort import Config
from rich import print as rich_print
from rich.prompt import Confirm, Prompt

from .errors import ProjectMakerError
from .maker import ApiComponent, Maker
from .namer import generate_declinations


class Args(NamedTuple):
    dev_dir: Path


def sigterm_handler(_, __):
    raise SystemExit(1)


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


def main(argv: Optional[Sequence[str]] = None):
    args = parse_args(argv)

    rich_print("[white bold on blue]\n  === Model W Project Maker ===  \n")

    context = dict(
        front={},
        api={},
        project_name={},
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

    context["front"]["enable"] = Confirm.ask("Will you have a front-end?", default=True)
    context["api"]["enable"] = Confirm.ask("Will you have a back-end?", default=True)

    if context["api"]["enable"]:
        context["api"]["wagtail"] = Confirm.ask("Would you like a Wagtail CMS?")
        context["api"]["celery"] = Confirm.ask("Do you expect using Celery queue?")
        context["api"]["channels"] = Confirm.ask(
            "Are you fancy enough to use WebSockets?"
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
                    known_first_party=[
                        context["project_name"]["snake"],
                    ],
                ),
            ),
        ]
    )

    maker.make(
        Path(__file__).parent.parent.parent.parent / "template",
        create_path,
        context,
    )

    rich_print("[green bold]Done!")


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
