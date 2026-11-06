"""
Utility functions for BDD testing.

This file is for utility functions that step definitions may need.
"""

import logging
import time
from collections.abc import Callable, Sequence
from typing import Any

from playwright.sync_api import FrameLocator, Locator, Page
from yaml import safe_load

logger = logging.getLogger(__name__)


def get_region(page: Page, region: str) -> Page | Locator:
    """
    Finds a region of the page by the name used in the feature files, through
    its accessible role (as a visitor using assistive technologies would).

    Args:
        page: The Playwright page
        region: The name of the region, e.g. "site header" or "mobile menu"
    """
    regions: dict[str, Callable[[], Page | Locator]] = {
        "page": lambda: page,
        "site header": lambda: page.get_by_role("banner"),
        # The drawer has its own "Main" navigation, hence the scoping
        "main navigation": lambda: page.get_by_role("banner").get_by_role(
            "navigation",
            name="Main",
        ),
        "site footer": lambda: page.get_by_role("contentinfo"),
        "mobile menu": lambda: page.get_by_role("dialog", name="Menu"),
    }

    assert region in regions, f"Unknown region '{region}', use one of {list(regions)}"

    return regions[region]()


def get_cms_preview(page: Page, preview: str) -> FrameLocator:
    """
    Finds the iframe of a preview in the Wagtail admin. They are all titled
    "Preview" (like the block chooser's one), so they are told apart by URL.

    Args:
        page: The Playwright page
        preview: Which preview, "page", "block" or "snippet"
    """
    iframes = {
        "page": 'iframe[src*="/pages/"][src*="/preview/"]',
        "block": 'iframe[src*="block-preview"]',
        "snippet": 'iframe[src*="/snippets/"][src*="/preview/"]',
    }

    assert preview in iframes, (
        f"Unknown preview '{preview}', use one of {list(iframes)}"
    )

    return page.frame_locator(iframes[preview])


def wait_until(
    check: Callable[[], bool],
    message: Callable[[], str],
    timeout: float = 5,
    interval: float = 0.1,
) -> None:
    """
    Waits for a condition that Playwright's `expect()` can't express (computed
    sizes, scroll positions...) to become true.

    Args:
        check: Returns True once the condition is met
        message: Gives the assertion message if it never is
        timeout: How long to wait, in seconds
        interval: How long to wait between two checks, in seconds
    """
    deadline = time.monotonic() + timeout

    while not check():
        assert time.monotonic() < deadline, message()
        time.sleep(interval)


def parse_datatable(
    datatable: Sequence[Sequence[str]],
    *,
    is_yaml: bool = False,
) -> list[dict[str, Any]]:
    """
    Parses a horizontal datatable into a list of dicts, one per row, keyed by the
    cells of the header (first) row.

    pytest-bdd gives the datatable of a step to its step function through the
    `datatable` argument, as a list of rows, each row being a list of cells.

    Args:
        datatable: The datatable, as received in the `datatable` step argument
        is_yaml: Parse each cell as YAML (eg. to get numbers and booleans)

    Example:
    -------
    ```gherkin
        Given the following users:
            | name | age |
            | foo  | 1   |
            | bar  | 22  |
    ```

    Gives `[{"name": "foo", "age": "1"}, {"name": "bar", "age": "22"}]`.

    """
    if not datatable:
        return []

    headers, *rows = datatable

    return [
        dict(
            zip(
                headers,
                (safe_load(value) if is_yaml else value for value in row),
                strict=False,
            ),
        )
        for row in rows
    ]


def parse_vertical_datatable(
    datatable: Sequence[Sequence[str]],
    *,
    is_yaml: bool = False,
) -> dict[str, Any]:
    """
    Parses a vertical datatable (one `| key | value |` row per item) into a dict.

    pytest-bdd gives the datatable of a step to its step function through the
    `datatable` argument, as a list of rows, each row being a list of cells.

    Args:
        datatable: The datatable, as received in the `datatable` step argument
        is_yaml: Parse each value as YAML (eg. to get numbers and booleans)

    Example:
    -------
    ```gherkin
        Given I am the following user:
            | email    | good2@user.com |
            | password | correct        |
    ```

    Gives `{"email": "good2@user.com", "password": "correct"}`.

    """
    data: dict[str, Any] = {}

    for row in datatable:
        if not row:
            continue

        value = row[1] if len(row) > 1 else ""
        data[row[0]] = safe_load(value) if is_yaml else value

    return data


def cast_to_bool(text: str) -> bool:
    """
    Casts a string to a boolean.

    Useful for string values in datatables that need to be treated as boolean

    Args:
        text (str): The text to cast
    """
    truthy = [
        "true",
        "yes",
        "1",
        "y",
        "x",
        "[x]",
        "on",
        "enable",
        "enabled",
        "active",
        "success",
    ]
    falsy = [
        "false",
        "no",
        "0",
        "",
        "[]",
        "[ ]",
        "n",
        "off",
        "disable",
        "disabled",
        "inactive",
        "failure",
    ]

    if text.lower() not in truthy + falsy:
        msg = (
            f"Cannot cast '{text}' to a boolean.  Please use one of {truthy} or "
            f"{falsy}, or extend cast_to_bool()"
        )
        raise ValueError(msg)

    return text.lower() in truthy


def key_values_to_table(event: dict[str, str]) -> str:
    """Prettify an object with key values to a nice HTML table."""
    table_html = "<table border='1' style='border-collapse: collapse; width: 100%;'>"
    table_html += "<thead><tr><th>Key</th><th>Value</th></tr></thead>"
    table_html += "<tbody>"

    for key, value in event.items():
        table_html += f"<tr><td>{key}</td><td>{value}</td></tr>"

    table_html += "</tbody></table>"

    return table_html


def event_a_subset_of_event_b(event_a: dict[str, str], event_b: dict[str, str]) -> bool:
    """
    Checks if event a is a subset of event b.
    ie. all of the keys and values in event a are present in event b, but not
    necessarily vice versa.
    """
    return all(event_b.get(key, "") == value for key, value in event_a.items())


def event_a_is_equal_to_event_b(
    event_a: dict[str, str],
    event_b: dict[str, str],
    ignore_keys: Sequence[str] = (),
) -> bool:
    """
    Checks if event a is equal to event b.
    ie. all of the keys and values in event a are present in event b, and vice
    versa.
    However, any keys in ignore_keys are ignored.
    """
    event_a_minus_ignore_keys = {
        key: value for key, value in event_a.items() if key not in ignore_keys
    }
    event_b_minus_ignore_keys = {
        key: value for key, value in event_b.items() if key not in ignore_keys
    }

    # Check no keys are missing
    missing_keys = set(event_a_minus_ignore_keys.keys()) - set(
        event_b_minus_ignore_keys.keys(),
    )
    if len(missing_keys) > 0:
        logger.error("Missing keys: %s", missing_keys)
        return False

    # Check no extra keys are present
    extra_keys = set(event_b_minus_ignore_keys.keys()) - set(
        event_a_minus_ignore_keys.keys(),
    )
    if len(extra_keys) > 0:
        logger.error("Extra keys: %s", extra_keys)
        return False

    # Check no values are different
    different_keys = [
        key
        for key in event_a_minus_ignore_keys
        if event_a_minus_ignore_keys.get(key) != event_b_minus_ignore_keys.get(key)
    ]

    if len(different_keys) > 0:
        logger.error("Different keys: %s", different_keys)
        for key in different_keys:
            logger.error(
                "%s: actual(%s), expected(%s)",
                key,
                event_b.get(key),
                event_a.get(key),
            )
        return False

    return True


def is_event_in_data_layer(
    target_event: dict[str, any],
    get_events: Callable[[], list[dict[str, any]]],
) -> bool:
    """
    Gets events (ie. dataLayer) via the get_events function.
    Checks that the target_event is one of the events.

    Note: Events could have auto-generated keys, which should be ignored.
          Therefore, update the ignore_keys list to include any as necessary.

    Args:
        target_event (dict[str, any]): The event to look for
        get_events (Callable): A function that gets the events from the page

    Returns:
        dict[str, str]: The data layer event if found, else None
    """
    ignore_keys = ["gtm.uniqueEventId"]

    # Repeat to allow for the dataLayer to be populated
    i = 0
    max_tries = 2
    event_exists = False

    while i < max_tries and not event_exists:
        events = get_events()
        logger.debug("all events on attempt %s: %s", i, events)

        event_exists = any(
            event_a_is_equal_to_event_b(
                target_event,
                event,
                ignore_keys=ignore_keys,
            )
            for event in events
        )

        if not event_exists:
            logger.debug("event not found on attempt %s", i)
            i += 1
            time.sleep(1)
    return event_exists
