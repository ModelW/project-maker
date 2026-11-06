"""
The setup wizard: options on the left, a live preview of the project on the
right, then the generation with its progress.
"""

import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import ClassVar

from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.validation import ValidationResult, Validator
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    Static,
    Tree,
)
from textual.widgets.tree import TreeNode

from ..generate import TEMPLATE, build_maker
from ..maker._base import Progress
from ..words import random_slug
from .options import (
    OVERRIDABLE,
    Options,
    check_admin_prefix,
    check_title,
)
from .picker import FolderPicker
from .preview import Folder, deployment, file_tree, planned_files, routes
from .progress import Generate, Outcome, ProgressScreen


def generate_project(target: Path, context: Mapping, progress: Progress) -> None:
    """
    Generates the project for real.

    Parameters
    ----------
    target
        Folder of the project
    context
        Context of the generation
    progress
        Receives the steps of the generation
    """

    build_maker().make(TEMPLATE, target, context, progress)


class Check(Validator):
    """Validates an input with one of the checks of the options module"""

    def __init__(self, check: Callable[[str], str | None]):
        super().__init__()
        self.check = check

    def validate(self, value: str) -> ValidationResult:
        if error := self.check(value):
            return self.failure(error)

        return self.success()


class WizardApp(App[Outcome | None]):
    """
    Collects the options, previews the project and generates it. Returns the
    outcome of the generation, or None if the user left before.
    """

    CSS_PATH = "wizard.tcss"
    TITLE = "Model W Project Maker"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+g", "create", "Create the project", priority=True),
        Binding("ctrl+o", "browse", "Change the folder"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(
        self,
        dev_dir: Path,
        dev_id: str,
        generate: Generate = generate_project,
    ):
        super().__init__()
        self.dev_id = dev_id
        self.generate = generate
        self.parent_dir = dev_dir.expanduser().absolute()
        #: Fields whose errors are shown (all of them after trying to create)
        self.touched: set[str] = set()
        #: Avoids reacting to the values the app sets itself
        self.updating = False

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main"):
            with VerticalScroll(id="form"):
                yield Static("Project", classes="section")
                yield Label("Name (free text, the other names derive from it)")
                yield Input(
                    placeholder="My Awesome Project",
                    id="title",
                    validators=[Check(check_title)],
                    compact=True,
                )
                yield Static(id="title-error", classes="error")

                yield Static("Name declinations", classes="section")
                yield Label("Derived from the name, check one to set it yourself")

                for declination in OVERRIDABLE:
                    yield Checkbox(
                        declination.style,
                        id=f"{declination.key}-override",
                        compact=True,
                    )
                    yield Input(
                        id=declination.key,
                        disabled=True,
                        classes="level-1",
                        validators=[Check(declination.check)],
                        compact=True,
                    )
                    yield Static(id=f"{declination.key}-error", classes="error level-1")

                yield Static("Location", classes="section")

                with Horizontal(id="location"):
                    yield Static(id="parent")
                    yield Button("Browse…", id="browse", compact=True)

                yield Static(id="target-error", classes="error")

                yield Static("Components", classes="section")
                yield Checkbox(
                    "Front-end — SvelteKit", value=True, id="front", compact=True
                )
                yield Checkbox("Back-end — Django", value=True, id="api", compact=True)
                yield Label(
                    "Admin URL prefix: /back/<prefix>/{admin,cms,ht}/",
                    classes="level-1",
                    id="admin-label",
                )

                with Horizontal(id="admin-prefix", classes="level-1"):
                    yield Input(
                        random_slug(),
                        id="admin_prefix",
                        validators=[Check(check_admin_prefix)],
                        compact=True,
                    )
                    yield Button("Shuffle", id="shuffle", compact=True)

                yield Static(id="admin_prefix-error", classes="error level-1")
                yield Checkbox(
                    "Wagtail CMS", id="wagtail", classes="level-1", compact=True
                )
                yield Checkbox(
                    "Demo snippet (shows how snippet previews work)",
                    id="demo_snippet",
                    classes="level-2",
                    compact=True,
                )
                yield Checkbox(
                    "Channels — WebSockets",
                    id="channels",
                    classes="level-1",
                    compact=True,
                )
                yield Static(id="components-error", classes="error")

                yield Button("Create the project", id="create", variant="success")

            with Vertical(id="preview"):
                with VerticalScroll(id="overview-scroll"):
                    yield Static(id="overview")

                yield Tree("", id="files")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#preview").border_title = "Preview"
        self.query_one("#form").border_title = "Options"
        self.query_one("#title").focus()
        self.refresh_all()

    # --- Reading the form ---

    def options(self) -> Options:
        """The options as currently set in the form"""

        def checked(id_: str) -> bool:
            return self.query_one(f"#{id_}", Checkbox).value

        def value(id_: str) -> str:
            return self.query_one(f"#{id_}", Input).value

        return Options(
            title=value("title"),
            overrides={
                d.key: value(d.key) for d in OVERRIDABLE if checked(f"{d.key}-override")
            },
            parent=self.parent_dir,
            front=checked("front"),
            api=checked("api"),
            wagtail=checked("wagtail"),
            channels=checked("channels"),
            demo_snippet=checked("demo_snippet"),
            admin_prefix=value("admin_prefix"),
        )

    # --- Reacting to changes ---

    @on(Input.Changed)
    def input_changed(self, event: Input.Changed) -> None:
        # Disabled inputs are the derived names, updated by the app itself
        if not self.updating and not event.input.disabled and event.input.id:
            self.touched.add(event.input.id)
            self.refresh_all()

    @on(Checkbox.Changed)
    def checkbox_changed(self, event: Checkbox.Changed) -> None:
        if self.updating:
            return

        for declination in OVERRIDABLE:
            if event.checkbox.id == f"{declination.key}-override":
                self.touched.add(declination.key)
                field_input = self.query_one(f"#{declination.key}", Input)

                if event.value:
                    field_input.focus()

        self.touched.add("components")
        self.refresh_all()

    def refresh_all(self) -> None:
        options = self.options()
        errors = options.errors()

        self.updating = True

        try:
            self.refresh_form(options, errors)
        finally:
            self.updating = False

        self.refresh_overview(options, errors)
        self.refresh_files(options)

    def refresh_form(self, options: Options, errors: dict[str, str]) -> None:
        names = options.names

        # Derived names follow the title until overridden
        for declination in OVERRIDABLE:
            key = declination.key
            overridden = self.query_one(f"#{key}-override", Checkbox).value
            field_input = self.query_one(f"#{key}", Input)
            field_input.disabled = not overridden

            if not overridden and field_input.value != names[key]:
                field_input.value = names[key]

        # Children are greyed out without their parent
        for id_ in ["admin-label", "admin_prefix", "shuffle", "wagtail", "channels"]:
            self.query_one(f"#{id_}").disabled = not options.api

        self.query_one("#demo_snippet").disabled = not options.wagtail_enabled

        self.query_one("#parent", Static).update(
            Text.assemble(
                ("Created in ", "dim"),
                (str(options.parent), "bold"),
                (f"{os.sep}{names['dashed'] or '?'}", "bold cyan"),
            )
        )

        fields = [
            "title",
            *(d.key for d in OVERRIDABLE),
            "admin_prefix",
            "target",
            "components",
        ]

        for field in fields:
            shown = field in self.touched or field == "target"
            error = errors.get(field) if shown else None
            widget = self.query_one(f"#{field}-error", Static)
            widget.update(error or "")
            widget.display = bool(error)

        self.query_one("#create", Button).disabled = bool(errors)

    def refresh_overview(self, options: Options, errors: dict[str, str]) -> None:
        names = options.names
        sections = []

        location = Table.grid(padding=(0, 1))
        location.add_column(style="dim")
        location.add_column()
        target = options.target

        if "target" in errors:
            status = Text(errors["target"], style="bold red")
        elif target.exists():
            status = Text("Empty folder, ready", style="green")
        else:
            status = Text("New folder", style="green")

        location.add_row("Folder", Text(str(target), style="bold"))
        location.add_row("Status", status)
        location.add_row("Author", self.dev_id)
        sections += [Text("Location", style="bold underline"), location, ""]

        def name(field: str) -> Text:
            style = "bold red strike" if field in errors else "bold cyan"
            return Text(names[field] or "?", style=style)

        table = Table.grid(padding=(0, 1))
        table.add_column(style="dim")
        table.add_column()
        table.add_column(style="dim italic")
        errors = {**errors, "natural": errors["title"]} if "title" in errors else errors
        table.add_row("natural", name("natural"), "title of the pages and admins")

        for declination in OVERRIDABLE:
            key = declination.key
            usage = name_usages(options).get(key, "")
            table.add_row(key, name(key), usage)

        sections += [Text("Names", style="bold underline"), table, ""]

        if url_list := routes(options):
            urls = Table.grid(padding=(0, 1))
            urls.add_column(style="bold")
            urls.add_column(style="dim")

            for route in url_list:
                urls.add_row(route.path, route.target)

            sections += [Text("URLs (single origin)", style="bold underline"), urls]
            sections.append("")

        deploy = deployment(options)

        if deploy.components:
            table = Table.grid(padding=(0, 1))
            table.add_column(style="dim")
            table.add_column()
            table.add_row("Components", ", ".join(deploy.components))
            table.add_row("Resources", ", ".join(deploy.resources) or "none")
            sections += [Text("Deployment (snow.yml)", style="bold underline"), table]

        self.query_one("#overview", Static).update(Group(*sections))

    def refresh_files(self, options: Options) -> None:
        tree = self.query_one("#files", Tree)
        files = planned_files(options.context(self.dev_id))
        root = file_tree(options.names["dashed"] or "?", files)

        # Keep what the user expanded when the tree gets rebuilt
        expanded = {
            path for node in walk(tree.root) if node.is_expanded and (path := node.data)
        }
        tree.clear()
        tree.root.set_label(folder_label(root, root.name))
        tree.root.data = ""
        add_folder(tree.root, root, "", expanded)
        tree.root.expand()
        tree.border_title = f"Files ({root.count})"

    # --- Actions ---

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool:
        """Creating and browsing only make sense from the main screen"""

        if action in {"create", "browse"}:
            return self.screen is self.screen_stack[0]

        return True

    @on(Button.Pressed, "#browse")
    def action_browse(self) -> None:
        self.push_screen(FolderPicker(self.parent_dir), self.folder_picked)

    def folder_picked(self, folder: Path | None) -> None:
        if folder is not None:
            self.parent_dir = folder
            self.refresh_all()

    @on(Button.Pressed, "#shuffle")
    def shuffle(self) -> None:
        self.query_one("#admin_prefix", Input).value = random_slug()

    @on(Button.Pressed, "#create")
    def action_create(self) -> None:
        options = self.options()

        if errors := options.errors():
            self.touched.update(errors)
            self.refresh_all()
            self.notify(
                "Fix the options first:\n" + "\n".join(errors.values()),
                severity="error",
            )
            return

        self.push_screen(
            ProgressScreen(options.target, options.context(self.dev_id), self.generate),
            self.exit,
        )


def name_usages(options: Options) -> dict[str, str]:
    """
    What the declinations of the name are used for in the generated project
    (the other ones are available to the template but unused so far).

    Parameters
    ----------
    options
        Wizard's options
    """

    snake = []

    if options.api:
        snake += ["Python package", "database"]

    if options.front:
        snake.append("npm package")

    return {"snake": ", ".join(snake), "dashed": "folder of the project"}


def walk(node: TreeNode):
    """
    All the nodes below the given one (included).

    Parameters
    ----------
    node
        Root of the walk
    """

    yield node

    for child in node.children:
        yield from walk(child)


def folder_label(folder: Folder, name: str) -> Text:
    """
    Label of a folder in the files tree.

    Parameters
    ----------
    folder
        The folder
    name
        Name to display (can be a chain of single-child folders)
    """

    return Text.assemble(
        (f"{name}/", "bold blue"),
        (f"  {folder.count}", "dim"),
    )


def add_folder(node: TreeNode, folder: Folder, path: str, expanded: set[str]) -> None:
    """
    Adds the content of a folder to the tree, folders first. Chains of
    single-folder folders are collapsed into one node (like GitHub does).

    Parameters
    ----------
    node
        Node to add the content to
    folder
        Folder to add
    path
        Path of the folder (identifies it across rebuilds)
    expanded
        Paths of the folders to show expanded
    """

    for name, child in sorted(folder.folders.items()):
        label = name

        while not child.files and len(child.folders) == 1:
            (sub_name, child), *_ = child.folders.items()
            label = f"{label}/{sub_name}"

        child_path = f"{path}/{label}"
        child_node = node.add(folder_label(child, label), data=child_path)
        add_folder(child_node, child, child_path, expanded)

        if child_path in expanded:
            child_node.expand()

    for name in sorted(folder.files):
        node.add_leaf(Text(name), data=None)
