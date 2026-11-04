"""
Test the utility functions that the BDD tester needs.

This file tests the utility functions that the tester may need.
"""

from pathlib import Path

import pytest
from django.utils import timezone
from pytest_bdd.parser import FeatureParser

from .fixtures import utils as fixtures_utils
from .report import utils as report_utils
from .report.reporter import Reporter
from .step_definitions import utils as step_def_utils

# Uses the global pytestmark variable to add the bdd_utils marker to all tests in
# this file. This means these tests can be specifically targetted with
# `pytest -m bdd_utils`.
pytestmark = [
    pytest.mark.bdd_utils,
]


########################
# FIXTURES UTILS TESTS #
########################


def test_should_strip_ansi_from_string():
    """ANSI color codes are removed from a string."""
    assert fixtures_utils.strip_ansi("\x1b[31mHello, World!\x1b[0m") == "Hello, World!"


def test_should_strip_ansi_from_string_with_multiple_ansi():
    """All the ANSI codes are removed, not only the first one."""
    assert (
        fixtures_utils.strip_ansi("\x1b[31mHello, \x1b[32mWorld!\x1b[0m")
        == "Hello, World!"
    )


def test_should_strip_ansi_from_string_with_escaped_ansi():
    """ANSI codes written with the octal escape are removed too."""
    assert fixtures_utils.strip_ansi("\033[33mHello, World!\033[0m") == "Hello, World!"


def test_should_strip_ansi_from_string_with_no_ansi():
    """A string without ANSI codes is left untouched."""
    assert fixtures_utils.strip_ansi("Hello, World!") == "Hello, World!"


def test_should_return_empty_string_when_given_empty_string():
    """Stripping ANSI codes from an empty string gives an empty string."""
    assert fixtures_utils.strip_ansi("") == ""


def test_should_return_empty_string_when_given_only_ansi():
    """A string made only of ANSI codes becomes empty."""
    assert fixtures_utils.strip_ansi("\x1b[31m\x1b[0m") == ""


def test_should_get_nuxt_3_server_url_localhost():
    """The server URL is extracted from Nuxt 3's startup line."""
    assert (
        fixtures_utils.get_nuxt_3_server_url("Listening on http://localhost:3000")
        == "http://localhost:3000"
    )


def test_should_get_nuxt_3_server_url_localhost_with_trailing_whitespace():
    """Trailing whitespace is not part of the extracted Nuxt 3 URL."""
    assert (
        fixtures_utils.get_nuxt_3_server_url("Listening on http://localhost:3000\n")
        == "http://localhost:3000"
    )


def test_should_get_nuxt_3_server_url_ipv6():
    """IPv6 server URLs are extracted from Nuxt 3's startup line."""
    assert (
        fixtures_utils.get_nuxt_3_server_url("Listening on http://[::]:3000")
        == "http://[::]:3000"
    )


def test_should_return_none_when_no_match():
    """None is returned when the line does not announce a Nuxt 3 URL."""
    assert fixtures_utils.get_nuxt_3_server_url("Local: http://localhost:3000/") is None


#########################
# REPORTING UTILS TESTS #
#########################


def test_should_get_singleton_instance():
    """Classes using SingletonMeta are only instantiated once."""

    class MyClass(metaclass=report_utils.SingletonMeta):
        """A class that should only have one instance."""

        def __init__(self, hello: str | None = None):
            self.hello = hello

    instance1 = MyClass("world")

    assert instance1 is MyClass()
    assert instance1.hello == "world"
    assert MyClass().hello == "world"


def test_datatable_to_arguments():
    """A datatable is converted to report rows, as written in the feature."""
    datatable = [
        ["key1", "key2"],
        ["value1", "value2"],
        ["value3", "value4"],
    ]
    expected = {
        "rows": [
            {"cells": ["key1", "key2"]},
            {"cells": ["value1", "value2"]},
            {"cells": ["value3", "value4"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_vertical_datatable_to_arguments():
    """A vertical datatable is converted to report rows, as written."""
    datatable = [
        ["key1", "value1"],
        ["key2", "value2"],
    ]
    expected = {
        "rows": [
            {"cells": ["key1", "value1"]},
            {"cells": ["key2", "value2"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_datatable_to_arguments_with_empty_values():
    """Empty cells are kept when converting a datatable."""
    datatable = [
        ["key1", "key2"],
        ["value1", ""],
        ["", "value2"],
    ]
    expected = {
        "rows": [
            {"cells": ["key1", "key2"]},
            {"cells": ["value1", ""]},
            {"cells": ["", "value2"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_datatable_to_arguments_with_escaped_pipes():
    """HTML-escaped pipes are unescaped in the report."""
    datatable = [["key &verbar; 1"], ["value &verbar; 1"]]
    expected = {
        "rows": [
            {"cells": ["key | 1"]},
            {"cells": ["value | 1"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_empty_datatable_to_arguments():
    """An empty datatable has no rows in the report."""
    assert report_utils.datatable_to_arguments([]) == {"rows": []}


def make_cucumber_report() -> list[dict]:
    """A cucumber JSON report, as written by pytest-bdd."""
    return [
        {
            "uri": "smoke-test.feature",
            "elements": [
                {
                    "id": "test_first[chromium]",
                    "name": "First",
                    "steps": [{"name": "step 1"}, {"name": "step 2"}],
                },
                {"id": "test_second[chromium]", "name": "Second", "steps": []},
            ],
        },
        {
            "uri": "a11y.feature",
            "elements": [
                {
                    "id": "test_first[chromium]",
                    "name": "First a11y",
                    "steps": [{"name": "a11y step"}],
                },
            ],
        },
    ]


def test_reporter_finds_scenario_by_feature_and_id():
    """Scenarios are found by the URI of their feature and their test id."""
    report = make_cucumber_report()
    reporter = Reporter()

    scenario = reporter.find_scenario(report, "a11y.feature", "test_first[chromium]")

    assert scenario is not None
    assert scenario["name"] == "First a11y"


def test_reporter_does_not_find_scenario_missing_from_report():
    """Scenarios missing from the report (eg. not run) are not found."""
    report = make_cucumber_report()
    reporter = Reporter()

    assert reporter.find_scenario(report, "a11y.feature", "test_other") is None
    assert reporter.find_scenario(report, "other.feature", "test_first") is None
    assert reporter.find_scenario([], "a11y.feature", "test_first") is None


def test_reporter_finds_step_by_index():
    """Steps are found by their index in their scenario."""
    report = make_cucumber_report()
    reporter = Reporter()

    step = reporter.find_step(report, "smoke-test.feature", "test_first[chromium]", 1)

    assert step == {"name": "step 2"}


def test_reporter_does_not_find_step_missing_from_report():
    """Steps which did not run are not found, nor are invalid indexes."""
    report = make_cucumber_report()
    reporter = Reporter()
    feature_uri = "smoke-test.feature"

    assert reporter.find_step(report, feature_uri, "test_first[chromium]", 2) is None
    assert reporter.find_step(report, feature_uri, "test_first[chromium]", -1) is None
    assert reporter.find_step(report, feature_uri, "test_first[chromium]", None) is None
    assert reporter.find_step(report, feature_uri, "test_second[chromium]", 0) is None
    assert reporter.find_step(report, feature_uri, "test_missing", 0) is None


###############################
# STEP DEFINITION UTILS TESTS #
###############################


def test_should_parse_datatable():
    """A horizontal datatable is parsed into a list of dicts."""
    assert step_def_utils.parse_datatable(
        [
            ["id", "name", "age"],
            ["1", "foo", "1"],
            ["2", "bar", "22"],
        ],
    ) == [
        {"id": "1", "name": "foo", "age": "1"},
        {"id": "2", "name": "bar", "age": "22"},
    ]


def test_should_parse_datatable_with_only_headers():
    """A horizontal datatable with only a header row has no items."""
    assert step_def_utils.parse_datatable([["id", "name"]]) == []


def test_should_parse_empty_datatable():
    """An empty horizontal datatable has no items."""
    assert step_def_utils.parse_datatable([]) == []


def test_should_parse_datatable_with_empty_values():
    """Empty cells of a horizontal datatable stay empty strings."""
    assert step_def_utils.parse_datatable(
        [
            ["id", "name", "age"],
            ["1", "foo", ""],
            ["", "bar", "22"],
            ["2", "", "22"],
        ],
    ) == [
        {"id": "1", "name": "foo", "age": ""},
        {"id": "", "name": "bar", "age": "22"},
        {"id": "2", "name": "", "age": "22"},
    ]


def test_should_parse_datatable_vertically():
    """A vertical datatable is parsed into a dict."""
    assert step_def_utils.parse_vertical_datatable(
        [
            ["id", "1"],
            ["name", "foo"],
        ],
    ) == {"id": "1", "name": "foo"}


def test_should_parse_datatable_with_empty_values_vertically():
    """Empty cells of a vertical datatable stay empty strings."""
    assert step_def_utils.parse_vertical_datatable(
        [
            ["id", "1"],
            ["name", "foo"],
            ["age", ""],
            ["foo", "bar"],
        ],
    ) == {"id": "1", "name": "foo", "age": "", "foo": "bar"}


def test_should_parse_vertical_datatable_with_missing_values():
    """Rows of a vertical datatable without a value give empty strings."""
    assert step_def_utils.parse_vertical_datatable([["id"], [], ["name", "foo"]]) == {
        "id": "",
        "name": "foo",
    }


def test_should_parse_empty_vertical_datatable():
    """An empty vertical datatable gives an empty dict."""
    assert step_def_utils.parse_vertical_datatable([]) == {}


def test_should_parse_datatable_with_yaml_string_only():
    """YAML parsing of a datatable keeps strings as strings."""
    actual = step_def_utils.parse_datatable(
        [["key1", "key2"], ["Value1", "Value2"]],
        is_yaml=True,
    )
    expected = [{"key1": "Value1", "key2": "Value2"}]

    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_datatable_with_yaml_with_numbers():
    """YAML parsing of a datatable converts numbers."""
    actual = step_def_utils.parse_datatable(
        [["key1", "key2"], ["1", "2"]],
        is_yaml=True,
    )
    expected = [{"key1": 1, "key2": 2}]

    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_datatable_with_yaml_with_boolean():
    """YAML parsing of a datatable converts booleans."""
    actual = step_def_utils.parse_datatable(
        [["key1", "key2"], ["yes", "no"]],
        is_yaml=True,
    )
    expected = [{"key1": True, "key2": False}]
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_vertical_datatable_with_yaml_string_only():
    """YAML parsing of a vertical datatable keeps strings as strings."""
    actual = step_def_utils.parse_vertical_datatable(
        [["key1", "Value1"], ["key2", "Value2"]],
        is_yaml=True,
    )
    expected = {"key1": "Value1", "key2": "Value2"}
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_vertical_datatable_with_yaml_with_numbers():
    """YAML parsing of a vertical datatable converts numbers."""
    actual = step_def_utils.parse_vertical_datatable(
        [["key1", "1"], ["key2", "2"]],
        is_yaml=True,
    )
    expected = {"key1": 1, "key2": 2}
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_vertical_datatable_with_yaml_with_boolean():
    """YAML parsing of a vertical datatable converts booleans."""
    actual = step_def_utils.parse_vertical_datatable(
        [["key1", "yes"], ["key2", "no"]],
        is_yaml=True,
    )
    expected = {"key1": True, "key2": False}
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_datatables_of_a_feature_file(tmp_path: Path):
    """
    The datatables given by pytest-bdd (with comment lines and escaped pipes)
    are parsed by the helpers.
    """
    (tmp_path / "datatables.feature").write_text(
        "Feature: Datatables\n"
        "    Scenario: Datatables\n"
        "        Given I am the following user:\n"
        "            | email    | good2@user.com |\n"
        "            # A comment line\n"
        "            | is_admin | no             |\n"
        "        Then I should see the following models:\n"
        "            | Group name | Model name    |\n"
        "            | Auth       | Groups \\| Me |\n",
    )
    feature = FeatureParser(str(tmp_path), "datatables.feature").parse()
    vertical_step, horizontal_step = feature.scenarios["Datatables"].steps

    assert step_def_utils.parse_vertical_datatable(
        vertical_step.datatable.raw(),
    ) == {"email": "good2@user.com", "is_admin": "no"}
    assert step_def_utils.parse_datatable(horizontal_step.datatable.raw()) == [
        {"Group name": "Auth", "Model name": "Groups | Me"},
    ]


def test_cast_to_bool_true():
    """Truthy texts are cast to True."""
    assert step_def_utils.cast_to_bool("True") is True
    assert step_def_utils.cast_to_bool("true") is True
    assert step_def_utils.cast_to_bool("yes") is True
    assert step_def_utils.cast_to_bool("y") is True
    assert step_def_utils.cast_to_bool("1") is True


def test_cast_to_bool_false():
    """Falsy texts are cast to False."""
    assert step_def_utils.cast_to_bool("False") is False
    assert step_def_utils.cast_to_bool("false") is False
    assert step_def_utils.cast_to_bool("no") is False
    assert step_def_utils.cast_to_bool("n") is False
    assert step_def_utils.cast_to_bool("0") is False
    assert step_def_utils.cast_to_bool("") is False


def test_cast_to_bool_invalid():
    """Texts that are neither truthy nor falsy raise a ValueError."""
    with pytest.raises(ValueError, match="invalid"):
        step_def_utils.cast_to_bool("invalid")


def test_key_values_to_table():
    """A dict is rendered as an HTML table of keys and values."""
    event = {
        "category": "a category",
        "division": "d1",
    }
    expected = (
        "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        "<thead>"
        "<tr><th>Key</th><th>Value</th></tr>"
        "</thead>"
        "<tbody>"
        "<tr><td>category</td><td>a category</td></tr>"
        "<tr><td>division</td><td>d1</td></tr>"
        "</tbody>"
        "</table>"
    )
    assert step_def_utils.key_values_to_table(event) == expected


def test_event_a_subset_of_event_b():
    """An event is a subset of another if all its keys and values are in it."""
    event_a = {
        "category": "a category",
        "division": "d1",
    }
    event_b = {
        "category": "a category",
        "division": "d1",
        "event": "virtualpageview",
    }
    assert step_def_utils.event_a_subset_of_event_b(event_a, event_b) is True

    event_a = {
        "category": "a category",
        "division": "d1",
        "event": "virtualpageview",
    }
    event_b = {
        "category": "a category",
        "division": "d1",
        "event": "uaevent",
    }
    assert step_def_utils.event_a_subset_of_event_b(event_a, event_b) is False

    event_a = {
        "category": "a category",
        "division": "d1",
        "event": "virtualpageview",
    }
    event_b = {
        "category": "a category",
        "division": "d1",
    }
    assert step_def_utils.event_a_subset_of_event_b(event_a, event_b) is False


def test_event_a_is_equal_to_event_b_when_identical():
    """Identical events are subsets of each other."""
    event_a = {
        "category": "a category",
        "division": "d1",
    }
    event_b = {
        "category": "a category",
        "division": "d1",
    }
    assert step_def_utils.event_a_subset_of_event_b(event_a, event_b) is True


def test_event_a_is_equal_to_event_b_when_different():
    """Events with a different value are not subsets."""
    event_a = {
        "category": "a category",
        "division": "d1",
    }
    event_b = {
        "category": "a category",
        "division": "d2",
    }
    assert step_def_utils.event_a_subset_of_event_b(event_a, event_b) is False


def test_event_a_is_equal_to_event_b_when_ignore_keys():
    """Ignored keys are not taken into account when comparing events."""
    event_a = {
        "category": "a category",
        "division": "d1",
        "event": "virtualpageview",
    }
    event_b = {
        "category": "a category",
        "division": "d1",
        "event": "uaevent",
    }
    assert (
        step_def_utils.event_a_is_equal_to_event_b(
            event_a,
            event_b,
            ignore_keys=["event"],
        )
        is True
    )


def test_event_a_is_equal_to_event_b_when_subset_of_event_b():
    """An event is not equal to a strict superset of itself."""
    event_a = {
        "category": "a category",
        "division": "d1",
    }
    event_b = {
        "category": "a category",
        "division": "d1",
        "event": "uaevent",
    }
    assert step_def_utils.event_a_is_equal_to_event_b(event_a, event_b) is False


def mock_data_layer() -> list[dict[str, any]]:
    """
    A function to mock getting the events from the page.
    The first event yielded will be a load event, simulating first page load.
    """
    yield {
        "event": "gtm.js",
        "gtm.start": int(timezone.now().timestamp() * 1000),
        "gtm.uniqueEventId": 1,
    }
    yield {
        "event": "gtm.dom",
        "gtm.uniqueEventId": 2,
    }
    yield {
        "event": "gtm.load",
        "gtm.uniqueEventId": 3,
    }
    yield {
        "category": "a category",
        "division": "d1",
        "event": "virtualpageview",
        "gtm.uniqueEventId": 4,
    }
    yield {
        "category": "a category",
        "division": "d1",
        "event": "uaevent",
        "gtm.uniqueEventId": 5,
    }
    yield {
        "category": "a category",
        "division": "d2",
        "event": "virtualpageview",
        "gtm.uniqueEventId": 6,
    }


def test_check_event_in_data_layer():
    """Events are looked up in the (mocked) data layer."""
    assert (
        step_def_utils.is_event_in_data_layer(
            {"category": "a category", "division": "d1", "event": "virtualpageview"},
            mock_data_layer,
        )
        is True
    )

    assert (
        step_def_utils.is_event_in_data_layer(
            {"category": "a category", "division": "d1", "event": "uaevent"},
            mock_data_layer,
        )
        is True
    )
    assert (
        step_def_utils.is_event_in_data_layer(
            {"category": "a category", "division": "d3", "event": "uaevent"},
            mock_data_layer,
        )
        is False
    )
    assert (
        step_def_utils.is_event_in_data_layer(
            {"category": "a category", "division": "d3", "event": "virtualpageview"},
            mock_data_layer,
        )
        is False
    )
