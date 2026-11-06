from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..maker._base import Progress

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

#: Generates the project: (target, context, progress) -> None
Generate = Callable[[Path, Mapping, Progress], None]


@dataclass(frozen=True)
class Outcome:
    """How the generation went"""

    target: Path
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class Step:
    """A step of the generation, as reported by the Maker"""

    name: str
    start: float
    end: float | None = None


class ProgressScreen(Screen[Outcome]):
    """
    Runs the generation in a thread and shows its steps as they happen, then
    the outcome. Dismissed with the Outcome once the user is done reading.
    """

    def __init__(self, target: Path, context: Mapping, generate: Generate):
        super().__init__()
        self.target = target
        self.context = context
        self.generate = generate
        self.steps: list[Step] = []
        self.started = monotonic()
        self.outcome: Outcome | None = None
        self.frame = 0

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="progress"):
            yield Static(
                Text.assemble("Creating ", (str(self.target), "bold")),
                classes="title",
            )
            yield Static(id="progress-steps")
            yield Static(id="progress-outcome")

            with VerticalScroll(id="progress-error"):
                yield Static(id="progress-error-text")

            with Horizontal(classes="buttons"):
                yield Button("Done", id="progress-done", variant="success")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#progress-done").display = False
        self.query_one("#progress-error").display = False
        self.set_interval(0.1, self.tick)
        self.run_generation()

    @work(thread=True, exit_on_error=False)
    def run_generation(self) -> None:
        def progress(step: str) -> None:
            self.app.call_from_thread(self.add_step, step)

        try:
            self.generate(self.target, self.context, progress)
        except Exception as e:
            self.app.call_from_thread(self.finish, Outcome(self.target, f"{e}"))
        else:
            self.app.call_from_thread(self.finish, Outcome(self.target))

    def add_step(self, name: str) -> None:
        now = monotonic()

        if self.steps:
            self.steps[-1].end = now

        self.steps.append(Step(name, now))
        self.render_steps()

    def finish(self, outcome: Outcome) -> None:
        self.outcome = outcome

        if self.steps and outcome.success:
            self.steps[-1].end = monotonic()

        self.render_steps()
        elapsed = monotonic() - self.started
        done = self.query_one("#progress-done", Button)
        done.display = True

        if outcome.success:
            self.query_one("#progress-outcome", Static).update(
                Text.assemble(
                    ("All clean and tidy, you can code! ", "bold green"),
                    f"({elapsed:.0f}s)\n\n",
                    "Next: ",
                    (f"cd {outcome.target}", "bold"),
                    " and have a look at the README.",
                )
            )
        else:
            done.label = "Quit"
            done.variant = "error"
            self.query_one("#progress-outcome", Static).update(
                Text.assemble(
                    ("Sorry, something went wrong. ", "bold red"),
                    "What was generated so far is still in ",
                    (str(outcome.target), "bold"),
                    ".",
                )
            )
            self.query_one("#progress-error").display = True
            self.query_one("#progress-error-text", Static).update(
                Text(outcome.error or "")
            )

        done.focus()

    def tick(self) -> None:
        self.frame += 1

        if self.outcome is None:
            self.render_steps()

    def render_steps(self) -> None:
        text = Text()
        now = monotonic()

        for i, step in enumerate(self.steps):
            last = i == len(self.steps) - 1
            duration = (step.end or now) - step.start

            if step.end is not None:
                text.append("  ✓ ", style="green")
            elif self.outcome is not None and not self.outcome.success and last:
                text.append("  ✗ ", style="bold red")
            else:
                text.append(f"  {SPINNER[self.frame % len(SPINNER)]} ", style="cyan")

            text.append(step.name)
            text.append(f"  {duration:.1f}s\n", style="dim")

        self.query_one("#progress-steps", Static).update(text)

    @on(Button.Pressed, "#progress-done")
    def done(self) -> None:
        if self.outcome is not None:
            self.dismiss(self.outcome)
