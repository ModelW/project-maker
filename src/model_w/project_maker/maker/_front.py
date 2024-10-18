import re
from pathlib import Path
from typing import Mapping

from node_edge import NodeEngine
from pathspec import pathspec

from ._base import BaseComponent


def make_path_specs() -> pathspec.PathSpec:
    """
    We take the project's .gitignore file and tweak it to ignore anything that
    isn't part of the front-end. We also drop the packages-lock.json because
    we want something fresh when the user gets to it.
    """

    lines = [
        "*",
        "!/front/",
    ]

    with open(Path(__file__).parent.parent / "template" / ".gitignore") as f:
        lines.extend(f)

    lines.append("package-lock.json")
    lines.append("!/front/src/lib/")
    lines.append("DemoBlock.svelte")
    lines.append("DemoSubBlock.svelte")
    lines.append("DemoPage.svelte")

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


class FrontComponent(BaseComponent):
    path_specs = make_path_specs()

    def __init__(self):
        """
        Since we use prettier for formatting code, we need a Node Edge
        instance.
        """

        self.ne = NodeEngine(
            {
                "dependencies": {
                    "prettier": "^2.8.0",
                    "@prettier/plugin-php": "^0.19.0",
                    "prettier-plugin-svelte": "^2.7.0",
                }
            }
        )
        self.prettier = None

    def start(self) -> None:
        """
        Warming up Node Edge and getting a proxy to prettier.
        """

        self.ne.start()
        self.prettier = self.ne.import_from("prettier")

    def stop(self) -> None:
        """
        Kill Node Edge
        """

        self.ne.stop()

    def accept(self, path: Path, context: Mapping):
        """
        Accept front-end files if the front-end is enabled. We do a little bit
        of custom rules in case Wagtail is enabled or not: if it's enabled then
        we add the catchall page with the ServerTemplatedComponent while
        otherwise we just put a simple index page.
        """

        if not context["front"]["enable"]:
            return False

        if self.path_specs.match_file(path):
            return False

        if not context["api"]["wagtail"] and (
            path.name
            in [
                "cms.ts",
            ]
            or path.parent.name
            in [
                "[...cmsPath]",
            ]
            or path.parent.parent.name
            in [
                "cms",
            ]
        ):
            return False

        return True

    def post_process(self, root: Path, path: Path, context: Mapping) -> None:
        """
        Mainly, reformats everything using Prettier. But also does a lot of
        renaming of .env and stuff.
        """

        file_path = root / path

        if file_path.name == ".env-template":
            new_path = file_path.parent / ".env"

            with open(file_path, encoding="utf-8") as f, open(
                new_path, "w", encoding="utf-8"
            ) as g:
                g.write(f.read())

        if not re.compile(
            r".*\.([jt]sx?|json|md|vue|php|html?|svelte|ya?ml|(s?c|le)ss)$",
            re.IGNORECASE,
        ).match(file_path.name):
            return

        info = self.prettier.getFileInfo(f"{file_path}")

        if not (parser := info.get("inferredParser")):
            return

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        formatted = self.prettier.format(
            content,
            {
                "parser": parser,
                "trailingComma": "es5",
                "tabWidth": 4,
                "proseWrap": "always",
            },
        )

        if formatted == content:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(formatted)
