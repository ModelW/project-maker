from collections.abc import Mapping
from pathlib import Path

from pathspec import pathspec

from ._base import LOCAL_FILES, BaseComponent


def make_path_specs() -> pathspec.PathSpec:
    """
    Ignore anything that isn't part of the front-end, as well as local files
    (see LOCAL_FILES) and the demo components, which are only there to test
    the template itself.
    """

    lines = [
        "*",
        "!/front/",
    ]

    lines.extend(LOCAL_FILES)

    lines.append("DemoBlock.svelte")
    lines.append("DemoSubBlock.svelte")
    lines.append("DemoPage.svelte")
    lines.append("/front/src/lib/components/cms/blocks/Heading.svelte")

    return pathspec.PathSpec.from_lines("gitignore", lines)


#: Files that only make sense with Wagtail
WAGTAIL_SPECS = pathspec.PathSpec.from_lines(
    "gitignore",
    [
        "/front/src/lib/utils/cms.ts",
        "/front/src/lib/utils/runScripts.ts",
        "/front/src/lib/components/cms/",
        "/front/src/routes/(site)/(cms)/",
        "/front/src/routes/(preview)/",
        "/front/src/params/cmsPath.ts",
    ],
)

#: Files that only make sense with the demo snippet
DEMO_SNIPPET_SPECS = pathspec.PathSpec.from_lines(
    "gitignore",
    ["/front/src/lib/components/cms/snippets/DemoSnippet.svelte"],
)

#: Files that only make sense with the API (its generated client)
API_SPECS = pathspec.PathSpec.from_lines("gitignore", ["/front/src/lib/api/"])

#: Files having an alternative implementation for projects without API, as
#: (with API, without API)
NO_API_ALTERNATIVES = [
    (
        Path("front/src/lib/session/provider.ts"),
        Path("front/src/lib/session/provider.no-api.ts"),
    ),
    (
        Path("front/src/lib/session/types.ts"),
        Path("front/src/lib/session/types.no-api.ts"),
    ),
]
NON_CMS_PAGE = Path("front/src/routes/(site)/non-cms/+page.svelte")
INDEX_PAGE = Path("front/src/routes/(site)/+page.svelte")


class FrontComponent(BaseComponent):
    path_specs = make_path_specs()

    def accept(self, path: Path, context: Mapping):
        """
        Accept front-end files if the front-end is enabled. Then some files
        depend on the options:

        - Without Wagtail, all the CMS-related code goes away (routes,
          components, utils)
        - The demo snippet's component only comes with the demo snippet
        - The session provider depends on whether there is an API
        """

        if not context["front"]["enable"]:
            return False

        if self.path_specs.match_file(path):
            return False

        api_enabled = bool(context["api"]["enable"])
        wagtail_enabled = api_enabled and bool(context["api"]["wagtail"])
        demo_snippet = wagtail_enabled and bool(context["api"].get("demo_snippet"))

        if not wagtail_enabled and WAGTAIL_SPECS.match_file(path):
            return False

        if not demo_snippet and DEMO_SNIPPET_SPECS.match_file(path):
            return False

        if not api_enabled and API_SPECS.match_file(path):
            return False

        for with_api, without_api in NO_API_ALTERNATIVES:
            if path == (without_api if api_enabled else with_api):
                return False

        return True

    def target_sub_path(self, path: Path, context: Mapping) -> Path:
        """
        Without API, the placeholder session provider and types take the place
        of the API ones. Without Wagtail, the non-CMS page becomes the home page.
        """

        api_enabled = bool(context["api"]["enable"])
        wagtail_enabled = api_enabled and bool(context["api"]["wagtail"])

        for with_api, without_api in NO_API_ALTERNATIVES:
            if path == without_api:
                return with_api

        if path == NON_CMS_PAGE and not wagtail_enabled:
            return INDEX_PAGE

        return path

    def post_process(self, root: Path, path: Path, context: Mapping) -> None:
        """
        Creates the .env from the .env-template. Formatting is done by the
        Prettier component, once the whole project is generated.
        """

        file_path = root / path

        if file_path.name == ".env-template":
            new_path = file_path.parent / ".env"
            new_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
