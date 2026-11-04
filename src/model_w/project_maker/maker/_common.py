from collections.abc import Mapping
from pathlib import Path

from pathspec import pathspec

from ._base import LOCAL_FILES, BaseComponent


def make_path_specs() -> pathspec.PathSpec:
    """
    We just want to copy all the files that are neither in api nor front (but
    the .github directory is welcome)
    """

    return pathspec.PathSpec.from_lines(
        "gitignore",
        [
            "/*/",
            "!/.github/",
            *LOCAL_FILES,
        ],
    )


class CommonComponent(BaseComponent):
    """
    A component that will copy stuff present at the root of the template, like
    the .editorconfig file and other things of the same style.
    """

    path_specs = make_path_specs()

    def accept(self, path: Path, context: Mapping):
        if self.path_specs.match_file(path):
            return False

        # The E2E suite lives in the API (and goes through the router)
        if path == Path(".github/workflows/e2e.yml"):
            return bool(context["api"]["enable"])

        return True
