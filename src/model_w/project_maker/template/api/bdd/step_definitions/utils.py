"""
This file is for utility functions that step definitions may need.
"""

import re
from typing import List


def split_on_pipes(text: str) -> List[str]:
    """
    Splits a string on pipes and returns a list of the results

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
    split = [item.strip() for item in re.split(r"(?<!\\)\|", text)]

    # Remove splits from before the first pipe and after the last pipe
    if len(split) >= 2:
        return split[1:-1]


def parse_datatable_string(datatable_string: str, vertical=False):
    """
    As pytest-bdd doesn't support data tables, we need to do it manually,
    as data tables are very useful for testing, and we'd be seriously limited
    without them.

    """

    # Split the string into lines
    lines = datatable_string.strip().split("\n")
    # Remove leading and trailing whitespace from each line
    lines = [line.strip() for line in lines]

    if vertical:
        data = [split_on_pipes(line) for line in lines]
        data_dict = {}
        for item in data:
            key = item[0].strip()
            value = item[1].strip() if len(item) > 1 else ""
            data_dict[key] = value

        return data_dict
    else:
        # Extract headers from the first line
        headers = split_on_pipes(lines[0])

        # Extract rows from the remaining lines
        rows: List[str] = []
        for line in lines[1:]:
            values = split_on_pipes(line)
            if len(values) < len(headers):
                values.extend(
                    [""] * (len(headers) - len(values))
                )  # Extend values to match headers length
            row = dict(zip(headers, values))
            rows.append(row)

        return rows
