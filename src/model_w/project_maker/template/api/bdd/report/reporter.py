"""
This file extends the default cucumber JSON report to include standard features such
as `embeddings` which are missing from pytest-bdd's implementation.

Adding an embedding can make debugging easier, as it allows you to attach screenshots
to any step in a scenario.  Furthermore, it can be used to attach logs or any other
data to a step, which can be used to check the state of the application at any step
in the flow.
For example, checking the data layer at a certain point in the scenario.
This is done by using the `report` fixture and calling `attach` or `attach_screenshot`
methods.

Also, the videos and screenshots that Playwright generates are attached to the report,
respecting the playwright config that has been set.
ie. `--video --screenshot` flags in the `pytest` command / pyproject.toml.

The idea is to keep track of the current pytest-bdd feature, scenario, and step index by
incrementing them in the appropriate pytest-bdd `hooks.py` and then at the end of the
session, inserting them into the created JSON.

Finally, the JSON is converted to HTML using the `cucumber-html-reporter` npm package.
"""

import base64
import json
import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from node_edge import NodeEngine
from playwright.sync_api import Page

from bdd.report import utils

logger = logging.getLogger(__name__)

# Only need DEBUG level here when there's an issue with the reporter
logger.setLevel(logging.INFO)


MimeType = Literal[
    "text/plain",
    "text/html",
    "application/json",
    "image/png",
    "image/gif",
    "application/octet-stream",
]

RESET_INDEX = -1  # Starting index for features, scenarios, and steps


@dataclass
class StepEmbedding:
    """
    Represents an embedding in a step.

    Embeddings are used to attach data to a step in a scenario,
    such as screenshots or logs.

    See: https://javadoc.io/doc/net.masterthought/cucumber-reporting/5.5.3/net/masterthought/cucumber/json/Embedding.html
    """

    mime_type: MimeType
    data: str
    feature_index: int | None = None
    scenario_index: int | None = None
    step_index: int | None = None

    def to_json(self) -> dict:
        """Convert the embedding to a JSON object."""
        return {"data": self.data, "mime_type": self.mime_type}


@dataclass
class Step:
    """
    Represents a step in a scenario, which is useful for adding steps not supported in pytest-bdd such as Before and After.

    See: https://javadoc.io/doc/net.masterthought/cucumber-reporting/5.5.3/net/masterthought/cucumber/json/Step.html

    This is used to add additional steps to the report, such as Before and After steps, and also existing steps, to change
    properties such as name (to add the browser/device) or to prettify the data tables, so they can be read.
    """

    feature_index: int
    scenario_index: int
    step_index: int | None = None
    media_directory: Path | None = None

    hidden: bool = True
    keyword: str = ""
    name: str = ""
    status: str = ""
    duration: int = 0
    arguments: list[str] | None = None
    embeddings: list[StepEmbedding] | None = None

    def to_json(self) -> dict:
        """Convert the step to a JSON object."""
        return {
            "hidden": self.hidden,
            "keyword": self.keyword,
            "name": self.name,
            "match": {"location": "", "duration": self.duration},
            "result": {"status": self.status},
            "arguments": self.arguments or [],
            "embeddings": (
                [embedding.to_json() for embedding in self.embeddings]
                if self.embeddings
                else []
            ),
        }


@dataclass
class Scenario:
    """
    A scenario in a feature to update the name of the scenario created by pytest-bdd.
    For example, adding the browser/device to the scenario name.
    """

    feature_index: int
    scenario_index: int
    name: str = ""

    def to_json(self) -> dict:
        """Convert the scenario to a JSON object."""
        return {
            "name": self.name,
        }


class Reporter(metaclass=utils.SingletonMeta):
    """
    The reporter (singleton) for all features.

    The reporter is used to store additional data to the cucumber report,
    such as screenshots, videos and logs, and written to json at the end of the session.
    """

    results_dir = Path(__file__).parent / "results"
    media_dir = Path(results_dir) / "media"
    json_report_path = Path(results_dir) / "report.json"
    html_report_path = Path(results_dir) / "report.html"

    def __init__(self):
        self.is_running = False
        self.embeddings: list[StepEmbedding] = []
        self.additional_steps: list[Step] = []
        self.existing_steps: list[Step] = []
        self.existing_scenarios: list[Scenario] = []
        self.feature_uri: str = ""
        self.current_feature_index: int = RESET_INDEX
        self.current_scenario_index: int = RESET_INDEX
        self.current_step_index: int = RESET_INDEX
        self.create_json_file()
        self.remove_report_html()

    def start(self) -> None:
        """Start the reporter or does nothing if it is already running."""
        if not self.is_running:
            logger.debug("Starting reporter")
            self.is_running = True

    def attach(self, data: str, mime_type: MimeType = "text/plain") -> None:
        """Attach an embedding to the current step."""
        embedding = StepEmbedding(
            mime_type=mime_type,
            data=data,
            feature_index=self.current_feature_index,
            scenario_index=self.current_scenario_index,
            step_index=self.current_step_index,
        )
        self.embeddings.append(embedding)
        logger.debug("Attached %s", embedding)

    def update_existing_scenario(self, name: str, page: Page) -> None:
        """
        Add an existing scenario to the report with data to be modified at
        the end of the session.
        ie. adding the browser/device to the scenario name.
        """
        browser_name = page.context.browser.browser_type.name
        viewport = page.viewport_size

        scenario = Scenario(
            feature_index=self.current_feature_index,
            scenario_index=self.current_scenario_index,
            name=f"{name} [{browser_name}@{viewport['width']}x{viewport['height']}]",
        )
        self.existing_scenarios.append(scenario)
        logger.debug("Updated existing scenario %s", scenario)

    def update_existing_step(
        self,
        name: str,
        arguments: list[str] | None = None,
    ) -> None:
        """
        Add an existing step to the report with data to be modified at
        the end of the session. ie. formatting datatables.

        Args:
            arguments: The arguments of the step (used for prettifying data tables)
        """
        step = Step(
            feature_index=self.current_feature_index,
            scenario_index=self.current_scenario_index,
            step_index=self.current_step_index,
            name=name,
            arguments=arguments,
        )
        self.existing_steps.append(step)
        logger.debug("Updated existing step %s", step)

    def add_undefined_step(self, keyword: str, name: str, arguments: list[str]) -> None:
        """Add an undefined step to the report."""
        step = Step(
            feature_index=self.current_feature_index,
            scenario_index=self.current_scenario_index,
            arguments=arguments,
            name=name,
            keyword=keyword,
            status="undefined",
            hidden=False,
        )
        self.additional_steps.append(step)
        logger.debug("Added undefined step %s", step)

    def add_after_step(
        self,
        media_directory: str,
        name="",
        keyword="After",
    ) -> None:
        """
        Add a step to the report so media produced by Playwright
        can be attached to it.

        Args:
            media_directory: The directory where the media is stored
        """
        self.increment_step()
        step = Step(
            feature_index=self.current_feature_index,
            scenario_index=self.current_scenario_index,
            name=name,
            keyword=keyword,
            status="passed",
            embeddings=[],
            media_directory=media_directory,
        )
        self.additional_steps.append(step)
        logger.debug("Added After step %s", step)

    def attach_screenshot(self, page: Page, full_page=False) -> None:
        """Attach a screenshot to the current step."""
        screenshot_bytes = page.screenshot(full_page=full_page)
        png = base64.b64encode(screenshot_bytes).decode()
        self.attach(png, "image/png")
        logger.debug("Attached screenshot to step %s", self.current_step_index)

    def attach_image(self, image_bytes: bytes) -> None:
        """Attach an image to the current step."""
        png = base64.b64encode(image_bytes).decode()
        self.attach(png, "image/png")
        logger.debug("Attached image to step %s", self.current_step_index)

    def increment_feature(self) -> None:
        """Increment the current feature index."""
        self.current_feature_index += 1
        self.current_scenario_index = RESET_INDEX
        self.current_step_index = RESET_INDEX
        logger.debug("Incremented feature index to %s", self.current_feature_index)

    def increment_scenario(self) -> None:
        """Increment the current scenario index."""
        self.current_scenario_index += 1
        self.current_step_index = RESET_INDEX
        logger.debug("Incremented scenario index to %s", self.current_scenario_index)

    def increment_step(self) -> None:
        """Increment the current step index."""
        self.current_step_index += 1
        logger.debug("Incremented step index to %s", self.current_step_index)

    def remove_report_html(self) -> None:
        """Remove the report HTML file."""
        logger.debug("Removing previous HTML report")
        self.html_report_path.unlink(missing_ok=True)

    def insert_embeddings_into_report(self) -> None:
        """Merge the embeddings from the JSON file into the cucumber report."""
        with self.json_report_path.open() as file:
            report = json.load(file)

        for embedding in self.embeddings:
            embeddings_list = self.get_current_step_embeddings(report, embedding)
            embeddings_list.append(embedding.to_json())

        with self.json_report_path.open("w") as file:
            json.dump(report, file, indent=4)

    def insert_media_tags_into_after_steps(self) -> None:
        """Insert the video tags into the report's After steps."""
        logger.debug("Inserting media tags into %s", self.additional_steps)
        for step in self.additional_steps:
            if step.keyword == "Video":
                logger.debug("Inserting video into %s", step.name)
                media_tags = self.get_video_tags_of_directory(
                    self.media_dir / step.media_directory,
                )
                for tag in media_tags:
                    step.embeddings.append(
                        StepEmbedding(
                            mime_type="text/html",
                            data=tag,
                        ),
                    )

            if step.keyword == "Screenshot":
                logger.debug("Inserting media tags into %s", step.name)
                media_tags = self.get_img_tags_of_directory(
                    self.media_dir / step.media_directory,
                )
                for tag in media_tags:
                    step.embeddings.append(
                        StepEmbedding(
                            mime_type="text/html",
                            data=tag,
                        ),
                    )

    def insert_additional_steps_into_report(self) -> None:
        """Merge the additional steps to the cucumber report."""
        self.insert_media_tags_into_after_steps()

        with open(self.json_report_path) as file:
            report = json.load(file)

        for step in self.additional_steps:
            feature: dict = report[step.feature_index]
            scenario: dict = feature["elements"][step.scenario_index]
            steps: list[dict] = scenario["steps"]

            if step.keyword == "Before":
                steps.insert(0, step.to_json())
            else:
                steps.append(step.to_json())

        with open(self.json_report_path, "w") as file:
            json.dump(report, file, indent=4)

    def update_existing_steps_in_json(self) -> None:
        """
        Merge the data stored in the existing steps to the cucumber report
        For example, prettifying datatables etc.
        """
        with open(self.json_report_path) as file:
            report = json.load(file)

        for existing_step in self.existing_steps:
            feature: dict = report[existing_step.feature_index]
            scenario: dict = feature["elements"][existing_step.scenario_index]
            step: dict = scenario["steps"][existing_step.step_index]

            if existing_step.arguments:
                step["name"] = existing_step.name
                step.setdefault("arguments", []).append(existing_step.arguments)

        with open(self.json_report_path, "w") as file:
            json.dump(report, file, indent=4)

    def update_existing_scenarios_in_json(self) -> None:
        """
        Merge the data stored in the existing scenarios to the cucumber report
        For example, adding the browser/device to the scenario name.
        """
        with open(self.json_report_path) as file:
            report = json.load(file)

        for existing_scenario in self.existing_scenarios:
            feature: dict = report[existing_scenario.feature_index]
            scenario: dict = feature["elements"][existing_scenario.scenario_index]
            scenario["name"] = existing_scenario.name

        with open(self.json_report_path, "w") as file:
            json.dump(report, file, indent=4)

    def create_json_file(self) -> None:
        """Create the JSON file for the report."""
        with self.json_report_path.open("w") as file:
            json.dump([], file)

    def get_current_step_embeddings(
        self,
        report: dict,
        embedding: StepEmbedding,
    ) -> dict:
        """Get the embeddings for the current step."""
        feature_index: int = embedding.feature_index
        scenario_index: int = embedding.scenario_index
        step_index: int = embedding.step_index

        feature = report[feature_index]
        scenario = feature["elements"][scenario_index]
        step = scenario["steps"][step_index]

        return step.setdefault("embeddings", [])

    def get_filepaths_in_directory(
        self,
        directory: Path,
        extension: str,
    ) -> Iterator[Path]:
        """
        Get the video files in a directory relative to the media directory.

        Args:
            directory: The directory to search
            extension: The file extension to search for (e.g. "webm")

        Returns:
            A list of file relative paths to the media directory

        Note: An extension can have a . prefix or not, it will be added if missing
        """
        extension = extension if extension.startswith(".") else f".{extension}"

        logger.debug("Searching for %s in %s", extension, directory)

        for file in directory.glob(f"*{extension}"):
            logger.debug("Found file: %s", file)
            yield file.relative_to(self.results_dir)

    def get_video_tags_of_directory(self, directory: Path) -> list[str]:
        """Get the videos in a directory."""
        return [
            f'<video src="{path}"'
            'style="max-width: 100%; height: auto;"'
            "controls></video>"
            for path in self.get_filepaths_in_directory(directory, "webm")
        ]

    def get_img_tags_of_directory(self, directory: Path) -> list[str]:
        """Get the images in a directory."""
        return [
            f'<img src="{path}"style="max-width: 100%; height: auto;"/>'
            for path in self.get_filepaths_in_directory(directory, "png")
        ]

    def generate_html_report(self) -> None:
        """Convert the JSON report to HTML."""
        with NodeEngine(
            {"dependencies": {"cucumber-html-reporter": "^7.1.1"}},
        ) as engine:
            generate = engine.import_from("cucumber-html-reporter", "generate")
            generate(
                {
                    "theme": "bootstrap",
                    "jsonFile": str(self.json_report_path),
                    "output": str(self.html_report_path),
                    "reportSuiteAsScenarios": True,
                    "scenarioTimestamp": True,
                    "launchReport": True,
                    "failedSummaryReport": True,
                },
            )

    def set_results_folder_permissions(self) -> None:
        """
        As we're sharing the same directory when running in docker and running
        locally, we update the permissions of the results folder to allow
        read/write access to everyone recursively.
        """
        self.results_dir.chmod(0o777)

        for root, dirs, files in os.walk(self.results_dir):
            for d in dirs:
                (Path(root) / d).chmod(0o777)
                logger.debug("Set 777 permissions on directory %s", Path(root) / d)
            for f in files:
                (Path(root) / f).chmod(0o666)
                logger.debug("Set 666 permissions on file %s", Path(root) / f)

    def __str__(self) -> str:
        return (
            f"Reporter - Running: {self.is_running}, "
            f"Embeddings: {len(self.embeddings)}, "
            f"Additional Steps: {len(self.additional_steps)}, "
            f"Existing Steps: {len(self.existing_steps)}, "
            f"JSON Report Path: {self.json_report_path}, "
            f"HTML Report Path: {self.html_report_path}"
        )

    def __repr__(self) -> str:
        return "Reporter()"
