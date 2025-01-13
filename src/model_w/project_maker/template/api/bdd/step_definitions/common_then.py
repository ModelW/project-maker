"""
These are the common then steps that can be used in scenarios.

- Then steps represent the assertions

Note: Different matchers can be used for the same step, to allow for more
      flexibility in the scenarios.  ie. to make the english make more sense.
      Be aware, the first matcher that matches will be used, so be careful if
      you have multiple matchers that could match the same step.
      When in doubt, play it simple and keep matchers unique to the step.
      ie. I should see the element "{data_testid}", and I should see the text "{data_testid}".
"""

import re

from django.utils import timezone
from playwright.sync_api import ConsoleMessage, Page, expect
from pytest_bdd import parsers, then
from pytest_django.live_server_helper import LiveServer

from . import utils


@then(parsers.cfparse('the text "{text}" should be the colour "{colour}"'))
def text_should_be_colour(page: Page, text: str, colour: str):
    """
    Check the colour of a text element.
    An example of how you can test inside the JS of a page.
    """
    element = page.get_by_text(text)
    colour = colour.lower()

    actual_colour = element.evaluate(
        """(element) => {
        const style = window.getComputedStyle(element)
        return style.color
        }""",
    )

    assert (
        actual_colour == colour
    ), f"Actual colour: {actual_colour}, Expected colour: {colour}"


@then(parsers.cfparse('I should be at the URL "{url}"'))
def at_exact_url(url: str, page: Page, front_server: str, live_server: LiveServer):
    """
    Check the current URL for an exact match.

    Note: A map is used to introduce special URLs you may need.
          The idea being to do a string replacement for special URLs
          eg. the api server's URL (which is random during testing)

    Example:
    -------
    ```gherkin
        Then I should be at the URL "https://example.com"
        Then I should be at the URL "http://localhost:3000/me"
        Then I should be at the URL "http://localhost:3000/me?q=1"
        Then I should be at the URL "<API_URL>"
    ```

    """
    # Map special URLs as required, else use the supplied URL
    SPECIAL_URLS = {
        "<API_URL>": live_server.url,
        "<FRONT_URL>": (
            front_server.rstrip("/")
            if not front_server.endswith(":80")
            else front_server.split(":80")[0]
        ),
    }

    for key, value in SPECIAL_URLS.items():
        url = url.replace(key, value)

    # Check with and without trailing slashes
    expect(page).to_have_url(re.compile(f"{re.escape(url)}/?$"))


@then(parsers.cfparse('I should be at a URL with "{url}"'))
def at_partial_url(url: str, page: Page):
    """
    Check the current URL for a partial match.

    Example:
    -------
    ```gherkin
        Then I should be at a URL with "example.com"
        Then I should be at a URL with "me"
        Then I should be at a URL with "q=1"
    ```

    """
    expect(page).to_have_url(re.compile(f".*{re.escape(url)}.*"))


@then(parsers.re(r'^I should see (?P<data_testid>[^"\n]+)$'))
@then(parsers.cfparse('I should see the "{data_testid}"'))
@then(parsers.cfparse('I should see "{data_testid}"'))
def should_see_element(data_testid: str, page: Page):
    """
    Check the page for an element with the expected element with data-testid.

    Note: we can pass special values to the testid, e.g. "today's date" which will
          be replaced with the current date in YYYY-MM-DD format.
    """
    special_values = {
        "today's date": timezone.now().strftime("%Y-%m-%d"),
    }
    for key, value in special_values.items():
        data_testid = data_testid.replace(key, value)

    expect(page.get_by_test_id(data_testid)).to_be_visible()


@then(parsers.re(r'^I should not see (?P<data_testid>[^"\n]+)$'))
@then(parsers.cfparse('I should not see the "{data_testid}"'))
@then(parsers.cfparse('I should not see "{data_testid}" button'))
@then(parsers.cfparse('I should not see "{data_testid}"'))
def should_not_see_element(data_testid: str, page: Page):
    """Check that the page does not contain the expected element with data-testid."""
    expect(page.get_by_test_id(data_testid)).not_to_be_visible()


@then(parsers.cfparse('I should see the text "{text}"'))
@then(parsers.cfparse('I should see the "{text}" message'))
def should_see_text(page: Page, text: str):
    """Check the page for the expected text."""
    expect(page.get_by_text(text)).to_be_visible()


@then(parsers.cfparse('I should not see the text "{text}"'))
@then(parsers.cfparse('I should not see the "{text}" message'))
def should_not_see_text(page: Page, text: str):
    """Check the page to make sure the expected text is not visible."""
    expect(page.get_by_text(text)).not_to_be_visible()


@then(parsers.cfparse("the {data_testid} should contain the text: {text}"))
@then(parsers.cfparse("{data_testid} should contain the text: {text}"))
def element_should_contain_text(data_testid: str, text: str, page: Page):
    """Check the text of an element with the expected data-testid."""
    expect(page.get_by_test_id(data_testid)).to_have_text(text)


@then("there should be no console errors")
def should_be_no_console_errors(page: Page, console: ConsoleMessage):
    """Check the console for any errors."""
    errors = [msg.text for msg in console if msg.type == "error"]
    assert not errors, f"Console errors: {errors}"


@then(parsers.cfparse("I should see the following Django admin models:\n{datatable}"))
def should_see_admin_models(page: Page, datatable):
    """
    Check the page for the expected admin models.

    Example:
    ```gherkin
        Then I should see the following admin models:
            | Group name                       | Model name    |
            | Authentication and Authorization | Groups        |
            | Celery Results                   | Group Results |
    ```

    """
    datatable = utils.parse_datatable_string(datatable)
    for row in datatable:
        group_name = row["Group name"]
        model_name = row["Model name"]

        # Find the caption element with the specified text
        group_caption = page.locator("caption").get_by_text(group_name)
        expect(group_caption).to_be_visible()

        # Find the parent table element containing the caption
        model_table = page.locator("table").filter(has=group_caption)
        expect(model_table).to_be_visible()

        # Find the model element within the table
        model_element = model_table.locator("a").get_by_text(model_name)
        expect(model_element).to_be_visible()
