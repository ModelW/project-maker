"""
Utility functions for BDD testing.

This file is for utility functions that step definitions may need.
"""

import logging
import re
import time
from collections.abc import Callable

from yaml import safe_load

logger = logging.getLogger(__name__)


def remove_model_w_template_engine_keywords(text: str) -> str:
    """
    Used to remove lines beginning with `# ::` as used in ModelW templates.

    Note: The line may have whitespace before the `#` and after the `::`
    """
    return re.sub(r"^\s*# ::.*\n", "", text, flags=re.MULTILINE)


def split_on_pipes(text: str) -> list[str]:
    r"""
    Splits a string on pipes and returns a list of the results.

    Note: Escaped pipes are ignored (ie. `\|` is not treated as a pipe)
          And leading and trailing whitespace is removed from each item
          And empty start and end items are removed

    Args:
        text (str): The text to split

    Returns:
        List[str]: The list of items

    Example:
        split_on_pipes("  | a | b | c |  ") -> ["a", "b", "c"]
    """
    values: list[str] = []

    split = [item.strip() for item in re.split(r"(?<!\\)\|", text)]

    # Remove splits from before the first pipe and after the last pipe
    if len(split) >= 2:  # noqa: PLR2004
        values = split[1:-1]

    return values


def parse_datatable_string(datatable_string: str, vertical=False, is_yaml=False):  # noqa: ANN001, FBT002
    """
    As pytest-bdd doesn't support data tables, we need to do it manually,
    as data tables are very useful for testing, and we'd be seriously limited
    without them.

    """
    # Remove ModelW template engine keywords
    datatable_string = remove_model_w_template_engine_keywords(datatable_string)
    # Split the string into lines
    lines = datatable_string.strip().split("\n")
    # Remove leading and trailing whitespace from each line
    lines = [line.strip() for line in lines]

    if vertical:
        data = [split_on_pipes(line) for line in lines]
        data_dict: dict[str, str] = {}
        for item in data:
            key = item[0].strip()
            value = item[1].strip() if len(item) > 1 else ""
            if is_yaml:
                value = safe_load(value)
            data_dict[key] = value

        return data_dict
    else:  # noqa: RET505
        # Extract headers from the first line
        headers = split_on_pipes(lines[0])

        # Extract rows from the remaining lines
        rows: list[dict[str, str]] = []
        for line in lines[1:]:
            values = split_on_pipes(line)
            if is_yaml:
                values = [safe_load(value) for value in values]
            row = dict(zip(headers, values, strict=False))
            rows.append(row)

        return rows


def get_datatable_from_step_name(step_name: str):
    """Returns the data table string from the step name."""
    return step_name.split("\n", 1)[-1] if "\n" in step_name else None


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
        msg = f"Cannot cast '{text}' to a boolean.  Please use one of {truthy} or {falsy}, or extend cast_to_bool()"
        raise ValueError(
            msg,
        )

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
    ie. all of the keys and values in event a are present in event b, but not necessarily vice versa.
    """
    return all(event_b.get(key, "") == value for key, value in event_a.items())


def event_a_is_equal_to_event_b(
    event_a: dict[str, str],
    event_b: dict[str, str],
    ignore_keys: list[str] = [],
) -> bool:
    """
    Checks if event a is equal to event b.
    ie. all of the keys and values in event a are present in event b, and vice versa.
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

