"""Helpers for the BDD report: singleton and data table/HTML formatting."""

from collections.abc import Sequence
from html import escape, unescape
from typing import ClassVar, TypedDict


class SingletonMeta(type):
    """
    A General purpose singleton class.

    To be used as a metaclass for a class that should
    only have one instance.

    Example:
    ```
    class MyClass(metaclass=SingletonMeta):
        pass
    ```
    """

    _instances: ClassVar[dict[type, object]] = {}

    def __call__(cls, *args, **kwargs):
        """
        If the class has not been instantiated, create an instance
        and store it in the _instances dictionary.
        Otherwise, return the instance that has already been created.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class DatatableRow(TypedDict):
    """A row of a data table, as expected by the Cucumber report."""

    cells: list[str]


class ReportDatatable(TypedDict):
    """A data table, as expected by the Cucumber report."""

    rows: list[DatatableRow]


def datatable_to_arguments(datatable: Sequence[Sequence[str]]) -> ReportDatatable:
    """
    Converts the datatable of a step (as given by pytest-bdd, a list of rows,
    each being a list of cells) to the format of the Cucumber report.

    The rows are kept as written in the feature file, so horizontal and
    vertical datatables are both displayed as they read in the feature file.

    Example:
    ```gherkin
        Given the following vertical datatable:
        | key1    | value1  |
        | key2    | value2  |
    ```
    Example:
    ```gherkin
        Given the following horizontal datatable:
        | key1   | key2   |
        | value1 | value2 |
    ```

    Args:
        datatable (Sequence[Sequence[str]]): The datatable to convert

    Returns:
        ReportDatatable: `{"rows": [{"cells": [...]}, ...]}`
    """
    return {"rows": [{"cells": [unescape(cell) for cell in row]} for row in datatable]}


def generate_a11y_report(results: dict) -> str:
    """Generate an HTML report from axe-core accessibility results."""
    if not results.get("violations"):
        return "No accessibility violations found<br>."

    html_report = []

    # Sort the violations by impact
    impact_levels = ["critical", "serious", "moderate", "minor"]
    impact_colours = {
        "critical": "#880808",
        "serious": "#CD7F32",
        "moderate": "#E1C16E",
        "minor": "#008080",
    }

    results["violations"] = sorted(
        results["violations"],
        key=lambda violation: impact_levels.index(violation["impact"]),
    )

    for violation in results["violations"]:
        colour = impact_colours.get(violation["impact"], "#000000")

        violation_id = escape(violation["id"])
        impact = escape(violation["impact"].capitalize())
        description = escape(violation.get("description", ""))
        help_url = escape(violation.get("helpUrl", "#"))

        html_report.append(
            f"<strong>{violation_id}</strong> - "
            f"<strong style='color: {colour}'>{impact}</strong><br>"
        )
        html_report.append(f"<em>Description: {description}</em><br>")
        html_report.append(f"<a href='{help_url}' target='_blank'>See more</a>")
        html_report.append("<ul>")

        for node in violation["nodes"]:
            target = ", ".join([escape(t) for t in node.get("target", [])])
            snippet = escape(node.get("html", ""))
            failure_summary = escape(node.get("failureSummary", ""))

            html_report.append("<li>")
            html_report.append(f"<strong>Target:</strong> {target}<br>")
            html_report.append(
                f"<strong>HTML Snippet:</strong><br><pre>{snippet}</pre><br>"
            )
            if failure_summary:
                html_report.append(
                    f"<strong>Failure Summary:</strong><br>{failure_summary}<br>"
                )
            html_report.append("</li>")

        html_report.append("</ul>")
        html_report.append("<hr>")

    return "".join(html_report)
