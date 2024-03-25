"""
This file contains all the pytest-bdd hooks custom behaviour.

The hooks are used to extend the default pytest-bdd behaviour, such as adding
extra information to the JSON reporter such as screenshots and logs.
"""

import base64
from typing import Any, Callable

import pytest
from pytest_bdd.parser import Feature, Scenario, Step
from slugify import slugify

from .report.reporter import Reporter

reporter = Reporter()


def pytest_sessionstart() -> None:
    """
    Called before the test loop is started.

    We use this to initialize the reporter, which is used to store additional data
    """


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

    if reporter.feature_uri != feature.rel_filename:
        reporter.feature_uri = feature.rel_filename
        reporter.increment_feature()

    reporter.increment_scenario()


def pytest_bdd_before_step(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., Any],
) -> None:
    """
    Called before step function is set up.
    We use this to keep track of which step we are currently executing,
    so we can add the correct additional data to the correct step in
    the report.
    """
    reporter.increment_step()


def pytest_bdd_after_step(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., Any],
    step_func_args: dict[str, Any],
) -> None:
    """
    Called after step function is executed.
    """


def pytest_bdd_after_scenario(
    request: pytest.FixtureRequest,
    feature: Feature,
    scenario: Scenario,
) -> None:
    """
    Called after scenario is executed successfully.
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
    """
    page = request.getfixturevalue("page")
    screenshot_bytes = page.screenshot(full_page=True)
    png = base64.b64encode(screenshot_bytes).decode()
    reporter.attach(png, "image/png")


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
        reporter.insert_embeddings_into_report()
        reporter.insert_additional_steps_into_report()
        reporter.generate_html_report()
