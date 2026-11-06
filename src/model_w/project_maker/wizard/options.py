"""
What the user chooses in the wizard, the names derived from it and the rules
they must follow. Nothing here depends on the user interface.
"""

import keyword
import os
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ..generate import build_context
from ..namer import generate_declinations, smart_split_name
from ..words import random_slug

SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
SNAKE_UP = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$")
# Like the namer, an underscore can only separate two numbers (v2_3Api)
CAMEL_LOW = re.compile(r"^[a-z][a-zA-Z0-9]*(_[0-9][a-zA-Z0-9]*)*$")
CAMEL_UP = re.compile(r"^[A-Z][a-zA-Z0-9]*(_[0-9][a-zA-Z0-9]*)*$")
DASHED = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
URL_SEGMENT = re.compile(r"^[a-z0-9]+([-_][a-z0-9]+)*$")

#: The Python package is also the database name and user in PostgreSQL, whose
#: identifiers are limited to 63 bytes
MAX_SNAKE_LENGTH = 63

#: Names already taken next to the Python package (in api/) or by the
#: dependencies it imports
RESERVED_PACKAGES = frozenset(
    {
        "bdd",
        "boto3",
        "channels",
        "conftest",
        "debug_toolbar",
        "django",
        "django_extensions",
        "drf_spectacular",
        "granian",
        "manage",
        "model_w",
        "ninja",
        "playwright",
        "procrastinate",
        "psycopg",
        "pydantic",
        "pytest",
        "redis",
        "rest_framework",
        "security",
        "sentry_sdk",
        "storages",
        "test",
        "tests",
        "wagtail",
    }
)

#: Prefixes already taken under /back/ by the API
RESERVED_ADMIN_PREFIXES = frozenset(
    {"__debug__", "api", "documents", "media", "static"}
)


def check_title(title: str) -> str | None:
    """
    The title is free text, but the other names are derived from its words.

    Parameters
    ----------
    title
        Human-readable name of the project
    """

    if not title.strip():
        return "Give your project a name"

    if not smart_split_name(title):
        return "The name needs at least one letter or digit"

    return None


def check_snake_format(name: str) -> str | None:
    """
    Without API, the snake name is only the npm package's name, which only
    needs the snake_case format.

    Parameters
    ----------
    name
        Candidate name
    """

    if not SNAKE.match(name):
        return (
            "Lowercase letters, digits and single underscores, starting with a "
            "letter (like my_project)"
        )

    return None


def check_snake(name: str) -> str | None:
    """
    The snake name is the Python package, the npm package and the database
    name (and user).

    Parameters
    ----------
    name
        Candidate name
    """

    if error := check_snake_format(name):
        return error

    if keyword.iskeyword(name) or keyword.issoftkeyword(name):
        return f'"{name}" is a Python keyword'

    if name in sys.stdlib_module_names:
        return f'"{name}" is a module of the Python standard library'

    if name in RESERVED_PACKAGES:
        return f'"{name}" is already used by the API (a dependency or a folder)'

    if len(name) > MAX_SNAKE_LENGTH:
        return f"At most {MAX_SNAKE_LENGTH} characters (it's also the database name)"

    return None


def check_dashed(name: str) -> str | None:
    """
    The dashed name is the name of the project's folder.

    Parameters
    ----------
    name
        Candidate name
    """

    if not DASHED.match(name):
        return "Lowercase letters, digits and single dashes (like my-project)"

    return None


def check_snake_up(name: str) -> str | None:
    """
    The SCREAMING_SNAKE_CASE declination (like for constants or environment
    variables).

    Parameters
    ----------
    name
        Candidate name
    """

    if not SNAKE_UP.match(name):
        return (
            "Uppercase letters, digits and single underscores, starting with a "
            "letter (like MY_PROJECT)"
        )

    return None


def check_camel_low(name: str) -> str | None:
    """
    The camelCase declination.

    Parameters
    ----------
    name
        Candidate name
    """

    if not CAMEL_LOW.match(name):
        return (
            "Letters and digits, starting with a lowercase letter (like "
            "myProject), underscores only between two numbers"
        )

    return None


def check_camel_up(name: str) -> str | None:
    """
    The PascalCase declination.

    Parameters
    ----------
    name
        Candidate name
    """

    if not CAMEL_UP.match(name):
        return (
            "Letters and digits, starting with an uppercase letter (like "
            "MyProject), underscores only between two numbers"
        )

    return None


def check_admin_prefix(prefix: str) -> str | None:
    """
    The admins (Django's and Wagtail's) and the health checks live under
    /back/<prefix>/.

    Parameters
    ----------
    prefix
        Candidate prefix
    """

    if not URL_SEGMENT.match(prefix):
        return (
            "Lowercase letters and digits, optionally separated by single dashes "
            "or underscores"
        )

    if prefix in RESERVED_ADMIN_PREFIXES:
        return f"/back/{prefix}/ is already used by the API"

    return None


def check_target(target: Path) -> str | None:
    """
    The project gets created in a new (or empty) folder.

    Parameters
    ----------
    target
        Folder of the project
    """

    if target.exists():
        if not target.is_dir():
            return f"{target} exists and isn't a folder"

        if any(target.iterdir()):
            return f"{target} already exists and isn't empty"

    existing = next(p for p in [target, *target.parents] if p.exists())

    if not existing.is_dir():
        return f"{existing} isn't a folder"

    if not os.access(existing, os.W_OK | os.X_OK):
        return f"You can't write in {existing}"

    return None


@dataclass(frozen=True)
class Options:
    """
    Everything the user decides in the wizard.
    """

    title: str = ""
    #: Declinations set by the user instead of derived from the title (keys
    #: from OVERRIDABLE)
    overrides: Mapping[str, str] = field(default_factory=dict)
    parent: Path = Path.home() / "dev"
    front: bool = True
    api: bool = True
    wagtail: bool = False
    channels: bool = False
    demo_snippet: bool = False
    admin_prefix: str = field(default_factory=random_slug)

    @property
    def wagtail_enabled(self) -> bool:
        """Wagtail only exists with the API"""

        return self.api and self.wagtail

    @property
    def channels_enabled(self) -> bool:
        """Channels only exists with the API"""

        return self.api and self.channels

    @property
    def demo_snippet_enabled(self) -> bool:
        """The demo snippet only exists with Wagtail"""

        return self.wagtail_enabled and self.demo_snippet

    @property
    def names(self) -> dict[str, str]:
        """
        All the declinations of the project's name, as expected in the context
        of the template, with the overrides applied.
        """

        return {
            "initial": self.title,
            **generate_declinations(self.title),
            **self.overrides,
        }

    @property
    def target(self) -> Path:
        """Folder in which the project gets created"""

        return self.parent / (self.names["dashed"] or "?")

    def errors(self) -> dict[str, str]:
        """
        What prevents the project from being created, by field ("title",
        the declinations, "admin_prefix", "components" and "target").
        """

        errors: dict[str, str] = {}

        if error := check_title(self.title):
            errors["title"] = error

        names = self.names

        for declination in OVERRIDABLE:
            overridden = declination.key in self.overrides

            # Derived from an invalid title: the title's error is enough
            if "title" in errors and not overridden:
                continue

            check = declination.check

            # Without API, the snake name is only the npm package's name
            if declination.key == "snake" and not self.api:
                check = check_snake_format

            if error := check(names[declination.key]):
                if not overridden:
                    error = f"Can't be derived from the name, set it yourself. {error}"

                errors[declination.key] = error

        if self.api and (error := check_admin_prefix(self.admin_prefix)):
            errors["admin_prefix"] = error

        if not self.front and not self.api:
            errors["components"] = "Pick at least a front-end or a back-end"

        if "dashed" not in errors and "title" not in errors:
            if error := check_target(self.target):
                errors["target"] = error

        return errors

    def context(self, dev_id: str) -> dict:
        """
        Context of the template for these options.

        Parameters
        ----------
        dev_id
            "Name <email>" of the developer
        """

        return build_context(
            project_name=self.names,
            front=self.front,
            api=self.api,
            wagtail=self.wagtail_enabled,
            channels=self.channels_enabled,
            demo_snippet=self.demo_snippet_enabled,
            admin_prefix=self.admin_prefix if self.api else None,
            dev_id=dev_id,
        )


@dataclass(frozen=True)
class Declination:
    """A declination of the project's name which the user can override"""

    #: Key in the template's context (project_name.<key>)
    key: str
    #: How the style is called
    style: str
    #: Validates a candidate name
    check: Callable[[str], str | None]


#: All the declinations of the name, except "natural" (the name itself) and
#: "natural_double_quoted" (only its escaped version)
OVERRIDABLE = [
    Declination("snake", "snake_case", check_snake),
    Declination("snake_up", "SCREAMING_SNAKE_CASE", check_snake_up),
    Declination("camel_low", "camelCase", check_camel_low),
    Declination("camel_up", "PascalCase", check_camel_up),
    Declination("dashed", "dashed-case", check_dashed),
]
