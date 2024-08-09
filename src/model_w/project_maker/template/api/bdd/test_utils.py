"""
Test the utility functions that the BDD tester needs.

This file tests the utility functions that the tester may need.
"""

import pytest
from django.utils import timezone

from .fixtures import utils as fixtures_utils
from .report import utils as report_utils
from .step_definitions import utils as step_def_utils

# Uses the global pytestmark variable to add the bdd_utils marker to all tests in this file.
# This means these tests can be specifically targetted with `pytest -m bdd_utils`.
pytestmark = [
    pytest.mark.bdd_utils,
]


########################
# FIXTURES UTILS TESTS #
########################


def test_should_strip_ansi_from_string():
    assert fixtures_utils.strip_ansi("\x1b[31mHello, World!\x1b[0m") == "Hello, World!"


def test_should_strip_ansi_from_string_with_multiple_ansi():
    assert (
        fixtures_utils.strip_ansi("\x1b[31mHello, \x1b[32mWorld!\x1b[0m")
        == "Hello, World!"
    )


def test_should_strip_ansi_from_string_with_escaped_ansi():
    assert fixtures_utils.strip_ansi("\033[33mHello, World!\033[0m") == "Hello, World!"


def test_should_strip_ansi_from_string_with_no_ansi():
    assert fixtures_utils.strip_ansi("Hello, World!") == "Hello, World!"


def test_should_return_empty_string_when_given_empty_string():
    assert fixtures_utils.strip_ansi("") == ""


def test_should_return_empty_string_when_given_only_ansi():
    assert fixtures_utils.strip_ansi("\x1b[31m\x1b[0m") == ""


def test_should_get_nuxt_3_server_url_localhost():
    assert (
        fixtures_utils.get_nuxt_3_server_url("Listening on http://localhost:3000")
        == "http://localhost:3000"
    )


def test_should_get_nuxt_3_server_url_localhost_with_trailing_whitespace():
    assert (
        fixtures_utils.get_nuxt_3_server_url("Listening on http://localhost:3000\n")
        == "http://localhost:3000"
    )


def test_should_get_nuxt_3_server_url_ipv6():
    assert (
        fixtures_utils.get_nuxt_3_server_url("Listening on http://[::]:3000")
        == "http://[::]:3000"
    )


def test_should_return_none_when_no_match():
    assert fixtures_utils.get_nuxt_3_server_url("Local: http://localhost:3000/") is None


#########################
# REPORTING UTILS TESTS #
#########################


def test_should_get_singleton_instance():
    class MyClass(metaclass=report_utils.SingletonMeta):
        """A class that should only have one instance."""

        def __init__(self, hello: str = None):
            self.hello = hello

    instance1 = MyClass("world")

    assert instance1 is MyClass()
    assert instance1.hello == "world"
    assert MyClass().hello == "world"


def test_vertical_datatable_to_arguments():
    datatable = {
        "key1": "value1",
        "key2": "value2",
    }
    expected = {
        "rows": [
            {"cells": ["key1", "key2"]},
            {"cells": ["value1", "value2"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_horizontal_datatable_to_arguments():
    datatable = [
        {"key1": "value1", "key2": "value2"},
        {"key1": "value3", "key2": "value4"},
    ]
    expected = {
        "rows": [
            {"cells": ["key1", "key2"]},
            {"cells": ["value1", "value2"]},
            {"cells": ["value3", "value4"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_datatable_to_arguments_with_empty_values():
    datatable = [
        {"key1": "value1", "key2": ""},
        {"key1": "", "key2": "value2"},
    ]
    expected = {
        "rows": [
            {"cells": ["key1", "key2"]},
            {"cells": ["value1", ""]},
            {"cells": ["", "value2"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_datatable_to_arguments_with_empty_values_vertically():
    datatable = {
        "key1": "value1",
        "key2": "",
    }
    expected = {
        "rows": [
            {"cells": ["key1", "key2"]},
            {"cells": ["value1", ""]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_datatable_to_arguments_with_escaped_pipes():
    datatable = [{"key &verbar; 1": "value &verbar; 1"}]
    expected = {
        "rows": [
            {"cells": ["key | 1"]},
            {"cells": ["value | 1"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


def test_datatable_to_arguments_with_escaped_pipes_vertically():
    datatable = {"key &verbar; 1": "value &verbar; 1"}
    expected = {
        "rows": [
            {"cells": ["key | 1"]},
            {"cells": ["value | 1"]},
        ],
    }
    assert report_utils.datatable_to_arguments(datatable) == expected


###############################
# STEP DEFINITION UTILS TESTS #
###############################


def test_remove_model_w_template_engine_keywords():
    assert (
        step_def_utils.remove_model_w_template_engine_keywords(
            """
        And I should see the following Django admin models:
            | Group name                       | Model name    |
            | Authentication and Authorization | Groups        |
            | Celery Results                   | Group Results |
            | Celery Results                   | Task Results  |
            | Taggit                           | Tags          |
        """,
        )
        == """
        And I should see the following Django admin models:
            | Group name                       | Model name    |
            | Authentication and Authorization | Groups        |
            | Celery Results                   | Group Results |
            | Celery Results                   | Task Results  |
            | Taggit                           | Tags          |
        """
    )


def test_remove_model_w_template_engine_keywords_with_no_keywords():
    assert (
        step_def_utils.remove_model_w_template_engine_keywords(
            """
        And I should see the following Django admin models:
            | Group name                       | Model name    |
            | Authentication and Authorization | Groups        |
            | Celery Results                   | Group Results |
            | Celery Results                   | Task Results  |
            | Taggit                           | Tags          |
        """,
        )
        == """
        And I should see the following Django admin models:
            | Group name                       | Model name    |
            | Authentication and Authorization | Groups        |
            | Celery Results                   | Group Results |
            | Celery Results                   | Task Results  |
            | Taggit                           | Tags          |
        """
    )


def test_remove_model_w_template_engine_keywords_with_no_string():
    assert step_def_utils.remove_model_w_template_engine_keywords("") == ""


def test_should_split_on_pipes():
    assert step_def_utils.split_on_pipes("| id | name |   age |") == [
        "id",
        "name",
        "age",
    ]


def test_should_split_on_pipes_with_extra_whitespace():
    assert step_def_utils.split_on_pipes("  | id  |    name   |   age | ") == [
        "id",
        "name",
        "age",
    ]


def test_should_split_on_pipes_with_extra_whitespace_and_newlines():
    assert step_def_utils.split_on_pipes("  | id  |    name   |   age | \n") == [
        "id",
        "name",
        "age",
    ]


def test_should_split_on_pipes_with_escaped_pipes():
    actual = "  | id  |    name \\| names   |   age |"
    expected = ["id", "name \\| names", "age"]
    assert step_def_utils.split_on_pipes(actual) == expected


def test_should_parse_datatable():
    assert step_def_utils.parse_datatable_string(
        """
        | id | name |   age |
        | 1  | foo  |  1    |
        | 2  | bar  |  22   |
        """,
    ) == [
        {"id": "1", "name": "foo", "age": "1"},
        {"id": "2", "name": "bar", "age": "22"},
    ]


def test_should_parse_datatable_with_extra_blank_lines():
    assert step_def_utils.parse_datatable_string(
        """

            
        | id | name |   age |
        | 1  | foo  |  1    |
        | 2  | bar  |  22   |



        
        """,
    ) == [
        {"id": "1", "name": "foo", "age": "1"},
        {"id": "2", "name": "bar", "age": "22"},
    ]


def test_should_parse_datatable_with_extra_blank_white_space():
    assert step_def_utils.parse_datatable_string(
        """

            
        | id  |    name   |   age | 
        | 1  |     foo  |  1        | 
        |    2  | bar  |    22   |    



        
        """,
    ) == [
        {"id": "1", "name": "foo", "age": "1"},
        {"id": "2", "name": "bar", "age": "22"},
    ]


def test_should_parse_datatable_vertically():
    assert step_def_utils.parse_datatable_string(
        """
    | id   | 1   |
    | name | foo |
    """,
        vertical=True,
    ) == {"id": "1", "name": "foo"}


def test_should_parse_datatable_horizontally_with_escaped_pipes():
    actual = """
    |id | name         | age |
    |1  | foo \\| bar  | 1   |
    """
    expected = [
        {"id": "1", "name": "foo \\| bar", "age": "1"},
    ]
    assert step_def_utils.parse_datatable_string(actual) == expected


def test_should_parse_datatable_vertically_with_escaped_pipes():
    actual = """
    | id   | 1   |
    | name | foo \\| bar |
    """
    expected = {"id": "1", "name": "foo \\| bar"}
    assert step_def_utils.parse_datatable_string(actual, vertical=True) == expected


def test_should_parse_datatable_with_empty_values():
    assert step_def_utils.parse_datatable_string(
        """
    | id | name | age |
    | 1  | foo  |     |
    |    | bar  |  22 |
    | 2  |      |  22 |
    """,
    ) == [
        {"id": "1", "name": "foo", "age": ""},
        {"id": "", "name": "bar", "age": "22"},
        {"id": "2", "name": "", "age": "22"},
    ]


def test_should_parse_datatable_with_empty_values_vertically():
    assert step_def_utils.parse_datatable_string(
        """
    | id   | 1      |
    | name | foo    |
    | age  |        |
    | foo  | bar    |
    """,
        vertical=True,
    ) == {"id": "1", "name": "foo", "age": "", "foo": "bar"}


def test_get_datatable_from_step():
    step_name = (
        "Given the following vertical datatable:\n| key1 | value1 |\n| key2 | value2 |"
    )
    assert (
        step_def_utils.get_datatable_from_step_name(step_name)
        == "| key1 | value1 |\n| key2 | value2 |"
    )


def test_get_datatable_from_step_without_datatable():
    step_name = "Given I am logged in as a CMS admin"
    assert step_def_utils.get_datatable_from_step_name(step_name) is None


def test_should_parse_datatable_with_yaml_string_only():
    datatable_string = """
        | key1   | key2   |
        | Value1 | Value2 |
    """
    actual = step_def_utils.parse_datatable_string(datatable_string, is_yaml=True)
    expected = [{"key1": "Value1", "key2": "Value2"}]

    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_datatable_with_yaml_with_numbers():
    datatable_string = """
        | key1 | key2 |
        | 1    | 2    |
    """
    actual = step_def_utils.parse_datatable_string(datatable_string, is_yaml=True)
    expected = [{"key1": 1, "key2": 2}]

    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_datatable_with_yaml_with_boolean():
    datatable_string = """
        | key1 | key2 |
        | yes  | no   |
    """
    actual = step_def_utils.parse_datatable_string(datatable_string, is_yaml=True)
    expected = [{"key1": True, "key2": False}]
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_vertical_datatable_with_yaml_string_only():
    datatable_string = """
        | key1   | Value1 |
        | key2   | Value2 |
    """
    actual = step_def_utils.parse_datatable_string(
        datatable_string,
        vertical=True,
        is_yaml=True,
    )
    expected = {"key1": "Value1", "key2": "Value2"}
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_vertical_datatable_with_yaml_with_numbers():
    datatable_string = """
        | key1 | 1 |
        | key2 | 2 |
    """
    actual = step_def_utils.parse_datatable_string(
        datatable_string,
        vertical=True,
        is_yaml=True,
    )
    expected = {"key1": 1, "key2": 2}
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_should_parse_vertical_datatable_with_yaml_with_boolean():
    datatable_string = """
        | key1 | yes |
        | key2 | no  |
    """
    actual = step_def_utils.parse_datatable_string(
        datatable_string,
        vertical=True,
        is_yaml=True,
    )
    expected = {"key1": True, "key2": False}
    assert actual == expected, f"Actual: {actual}, Expected: {expected}"


def test_cast_to_bool_true():
    assert step_def_utils.cast_to_bool("True") is True
    assert step_def_utils.cast_to_bool("true") is True
    assert step_def_utils.cast_to_bool("yes") is True
    assert step_def_utils.cast_to_bool("y") is True
    assert step_def_utils.cast_to_bool("1") is True


def test_cast_to_bool_false():
    assert step_def_utils.cast_to_bool("False") is False
    assert step_def_utils.cast_to_bool("false") is False
    assert step_def_utils.cast_to_bool("no") is False
    assert step_def_utils.cast_to_bool("n") is False
    assert step_def_utils.cast_to_bool("0") is False
    assert step_def_utils.cast_to_bool("") is False


def test_cast_to_bool_invalid():
    pytest.raises(ValueError, step_def_utils.cast_to_bool, "invalid")


def test_key_values_to_table():
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
