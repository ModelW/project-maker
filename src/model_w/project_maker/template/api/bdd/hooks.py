"""
This file contains all the pytest-bdd hooks custom behaviour.

The hooks are used to extend the default pytest-bdd behaviour, such as adding
extra information to the JSON reporter such as screenshots and logs.
"""

import base64
import logging
from collections.abc import Callable
from typing import Any

import pytest
import pytest_bdd
import pytest_bdd.exceptions
from playwright.sync_api import Page
from pytest_bdd.parser import Feature, Scenario, Step
from slugify import slugify

from .report import utils as report_utils
from .report.reporter import Reporter

logger = logging.getLogger(__name__)

reporter = Reporter()


def get_step_arguments(step: Step) -> list[report_utils.ReportDatatable]:
    """
    Get the arguments of a step (ie. its datatable) as expected by the cucumber
    report, which pytest-bdd does not include in its JSON report.
    """
    if step.datatable is None:
        return []

    return [report_utils.datatable_to_arguments(step.datatable.raw())]


def report_step_extras(step: Step) -> None:
    """
    Add the datatable and docstring of the current step to the report, so they
    are displayed nicely, as pytest-bdd does not include them in its JSON
    report.
    """
    arguments = get_step_arguments(step)

    if arguments or step.docstring is not None:
        reporter.update_existing_step(
            name=step.name,
            arguments=arguments,
            doc_string=step.docstring,
        )


def pytest_sessionstart() -> None:
    """Called before the test loop is started."""


def pytest_bdd_before_scenario(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
) -> None:
    """
    Called before scenario is executed.
    We use this to keep track of which feature and scenario we are currently
    executing, so we can add the correct additional data to the correct scenario
    in the report.
    """
    reporter.start()
    reporter.start_scenario(
        feature_uri=feature.rel_filename,
        scenario_id=request.node.name,
    )

    page: Page = request.getfixturevalue("page")

    reporter.update_existing_scenario(
        name=scenario.name,
        page=page,
    )


def pytest_bdd_before_step(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., Any],
) -> None:
    """
    Called before a step is executed, at the same time pytest-bdd adds it to its
    report (before its arguments are parsed, which may fail).
    We use this to keep track of which step we are currently executing,
    so we can add the correct additional data to the correct step in
    the report, such as its datatable and docstring.
    """
    reporter.increment_step()
    report_step_extras(step)


def pytest_bdd_after_scenario(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
) -> None:
    """
    Called after scenario is executed, whether it passed or failed.
    We use this to add a After steps for video and screenshot.
    """
    reporter.add_after_step(
        media_directory=slugify(request.node.nodeid),
        keyword="Video",
    )
    reporter.add_after_step(
        media_directory=slugify(request.node.nodeid),
        keyword="Screenshot",
    )


def pytest_bdd_step_error(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., Any],
    step_func_args: dict[str, Any],
    exception: Exception,
):
    """
    Called when a step fails.
    We use this to add a screenshot to the report at the failing step.
    Note: As only 1 screenshot per step is supported, we skip this
    if a screenshot is already attached to the step (for example a VR difference).
    """
    if reporter.current_step_has_image():
        logger.debug(
            "Skipping failure screenshot — image already attached to step %s",
            step,
        )
        return

    page = request.getfixturevalue("page")
    screenshot_bytes = page.screenshot(full_page=True)
    png = base64.b64encode(screenshot_bytes).decode()
    reporter.attach(png, "image/png")


def pytest_bdd_step_func_lookup_error(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    exception: Exception,
):
    """
    Called when a step lookup fails.
    We use this to add the correct status to the report at the failing step.
    """
    logger.exception(exception)
    if isinstance(exception, pytest_bdd.exceptions.StepDefinitionNotFoundError):
        reporter.add_undefined_step(
            step.keyword,
            step.name,
            get_step_arguments(step),
        )


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int | pytest.ExitCode,
) -> None:
    """
    Called after the entire session is finished.
    We use this to prepare the report by merging the additional data we want
    to include, and generating a HTML version.
    """
    if reporter.is_running:
        reporter.update_existing_steps_in_json()
        reporter.update_existing_scenarios_in_json()
        reporter.insert_embeddings_into_report()
        reporter.insert_additional_steps_into_report()
        reporter.generate_html_report()
        reporter.set_results_folder_permissions()
