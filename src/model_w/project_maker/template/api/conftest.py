"""
Global configuration of pytest is done in the [pyproject.toml](../pyproject.toml) file.
However, for more complicated configs that also need to be global, it can be added here.
"""

import os

import pytest

# Allow async code to be run in Django tests
# @see: https://github.com/microsoft/playwright-pytest/issues/29
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options to pytest."""
    group = parser.getgroup("general")
    group.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Update snapshots.",
    )
