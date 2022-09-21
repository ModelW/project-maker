#!/usr/bin/env python3
from signal import SIGTERM, signal
from sys import stderr

from rich import print as rich_print
from rich.prompt import Confirm, Prompt


class ProjectMakerError(Exception):
    pass


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


def main():
    rich_print("[white bold on blue]\n  === Model W Project Maker ===  \n")

    context = dict(
        front={},
        api={},
    )

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

    context["project_name"] = Prompt.ask("What is the project's name?")

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


def __main__():
    signal(SIGTERM, sigterm_handler)

    try:
        main()
    except KeyboardInterrupt:
        stderr.write("ok, bye\n")
        exit(1)
    except ProjectMakerError as e:
        stderr.write(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    __main__()
