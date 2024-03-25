"""
This file tests the utility functions that the tester may need.
"""

import pytest

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


###############################
# STEP DEFINITION UTILS TESTS #
###############################


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
    assert (
        step_def_utils.parse_datatable_string(
            """
        | id | name |   age |
        | 1  | foo  |  1    |
        | 2  | bar  |  22   |
        """
        )
        == [
            {"id": "1", "name": "foo", "age": "1"},
            {"id": "2", "name": "bar", "age": "22"},
        ]
    )


def test_should_parse_datatable_with_extra_blank_lines():
    assert (
        step_def_utils.parse_datatable_string(
            """

            
        | id | name |   age |
        | 1  | foo  |  1    |
        | 2  | bar  |  22   |



        
        """
        )
        == [
            {"id": "1", "name": "foo", "age": "1"},
            {"id": "2", "name": "bar", "age": "22"},
        ]
    )


def test_should_parse_datatable_with_extra_blank_white_space():
    assert (
        step_def_utils.parse_datatable_string(
            """

            
        | id  |    name   |   age | 
        | 1  |     foo  |  1        | 
        |    2  | bar  |    22   |    



        
        """
        )
        == [
            {"id": "1", "name": "foo", "age": "1"},
            {"id": "2", "name": "bar", "age": "22"},
        ]
    )


def test_should_parse_datatable_vertically():
    assert (
        step_def_utils.parse_datatable_string(
            """
    | id   | 1   |
    | name | foo |
    """,
            vertical=True,
        )
        == {"id": "1", "name": "foo"}
    )


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
    assert (
        step_def_utils.parse_datatable_string(
            """
    | id | name | age |
    | 1  | foo  |     |
    |    | bar  |  22 |
    | 2  |      |  22 |
    """
        )
        == [
            {"id": "1", "name": "foo", "age": ""},
            {"id": "", "name": "bar", "age": "22"},
            {"id": "2", "name": "", "age": "22"},
        ]
    )


def test_should_parse_datatable_with_empty_values_vertically():
    assert (
        step_def_utils.parse_datatable_string(
            """
    | id   | 1      |
    | name | foo    |
    | age  |        |
    | foo  | bar    |
    """,
            vertical=True,
        )
        == {"id": "1", "name": "foo", "age": "", "foo": "bar"}
    )
