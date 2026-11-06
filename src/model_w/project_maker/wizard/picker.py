from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Label, Static


class FolderTree(DirectoryTree):
    """A directory tree showing only the (non-hidden) folders"""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [p for p in paths if p.is_dir() and not p.name.startswith(".")]


def existing_folder(path: Path) -> Path:
    """
    The path itself if it's a folder, otherwise its closest existing parent.

    Parameters
    ----------
    path
        Any path
    """

    return next(p for p in [path, *path.parents] if p.is_dir())


class FolderPicker(ModalScreen[Path | None]):
    """
    Picks the folder in which the project's folder gets created. Returns the
    chosen folder, or None if cancelled.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "cancel", "Cancel"),
        Binding("backspace", "parent", "Parent folder", show=False),
    ]

    def __init__(self, start: Path):
        super().__init__()
        self.start = existing_folder(start.expanduser().absolute())

    def compose(self) -> ComposeResult:
        with Vertical(id="picker"):
            yield Static("Where should the project's folder go?", classes="title")
            yield Label("Type a path (Enter to browse it) or pick a folder below")
            yield Input(str(self.start), id="picker-path")
            yield FolderTree(self.start, id="picker-tree")

            with Horizontal(classes="buttons"):
                yield Button("↑ Parent", id="picker-parent")
                yield Button("⌂ Home", id="picker-home")
                yield Static(classes="spacer")
                yield Button("Cancel", id="picker-cancel")
                yield Button("Select", id="picker-select", variant="primary")

    def on_mount(self) -> None:
        self.query_one(FolderTree).focus()

    def browse(self, path: Path) -> None:
        """
        Shows the given folder (or its closest existing parent) in the tree.

        Parameters
        ----------
        path
            Folder to show
        """

        folder = existing_folder(path.expanduser().absolute())
        self.query_one(FolderTree).path = folder
        self.query_one("#picker-path", Input).value = str(folder)

    @on(DirectoryTree.DirectorySelected)
    @on(DirectoryTree.NodeHighlighted)
    def follow_tree(self, event) -> None:
        node = event.node

        if node.data is not None:
            self.query_one("#picker-path", Input).value = str(node.data.path)

    @on(Input.Submitted, "#picker-path")
    def follow_input(self, event: Input.Submitted) -> None:
        self.browse(Path(event.value))

    @on(Button.Pressed, "#picker-parent")
    def action_parent(self) -> None:
        self.browse(self.query_one(FolderTree).path.parent)

    @on(Button.Pressed, "#picker-home")
    def go_home(self) -> None:
        self.browse(Path.home())

    @on(Button.Pressed, "#picker-cancel")
    def action_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#picker-select")
    def select(self) -> None:
        path = Path(self.query_one("#picker-path", Input).value).expanduser()

        if not path.is_dir():
            self.notify(f"{path} isn't an existing folder", severity="error")
            return

        self.dismiss(path.absolute())
