"""
Utility functions for BDD testing.

This file is for utility functions that step definitions may need.
"""

import re

from yaml import safe_load


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
