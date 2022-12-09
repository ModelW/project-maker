from pathlib import Path
from typing import Mapping

from pathspec import pathspec

from ._base import BaseComponent


def make_path_specs() -> pathspec.PathSpec:
    """
    We just want to copy all the files that are neither in api nor front
    """

    return pathspec.PathSpec.from_lines(
        "gitwildmatch",
        [
            "/*/",
        ],
    )


class CommonComponent(BaseComponent):
    """
    A component that will copy stuff present at the root of the template, like
    the .editorconfig file and other things of the same style.
    """

    path_specs = make_path_specs()

    def accept(self, path: Path, context: Mapping):
        return not self.path_specs.match_file(path)
