"""
These are the common then steps that can be used in scenarios.

- Then steps represent the assertions
"""

import re

from playwright.sync_api import ConsoleMessage, Page, expect
from pytest_bdd import parsers, then


@then(parsers.cfparse('the text "{text}" should be the colour "{colour}"'))
def text_should_be_colour(page: Page, text: str, colour: str):
    """
    A bit of hubris, but the point being to test that the Nuxt injection
    of the Wagtail served content is working as expected.

    Also a good example of how you can test inside the JS of a page
    """
    element = page.get_by_text(text)
    colour = colour.lower()

    actual_colour = element.evaluate(
        """(element) => {
        const style = window.getComputedStyle(element)
        return style.color
        }"""
    )

    assert (
        actual_colour == colour
    ), f"Actual colour: {actual_colour}, Expected colour: {colour}"


@then(parsers.cfparse('I should be at the URL "{url}"'))
def at_exact_url(url: str, page: Page):
    """
    Checks the current URL for an exact match

    Example:
        Then I should be at the URL "https://example.com"
        Then I should be at the URL "http://localhost:3000/me"
        Then I should be at the URL "http://localhost:3000/me?q=1"
    """
    expect(page).to_have_url(url)


@then(parsers.cfparse('I should be at a URL with "{url}"'))
def at_partial_url(url: str, page: Page):
    """
    Checks the current URL for a partial match

    Example:
        Then I should be at a URL with "example.com"
        Then I should be at a URL with "me"
        Then I should be at a URL with "q=1"
    """
    expect(page).to_have_url(re.compile(f".*{url}.*"))


@then(parsers.cfparse('I should see the "{data_testid}"'))
@then(parsers.cfparse('I should see "{data_testid}"'))
def should_see_element(data_testid: str, page: Page):
    """Checks the page for an element with the expected element with data-testid"""
    expect(page.get_by_test_id(data_testid)).to_be_visible()


@then(parsers.cfparse('I should not see the "{data_testid}"'))
@then(parsers.cfparse('I should not see "{data_testid}"'))
def should_not_see_element(data_testid: str, page: Page):
    """Checks that the page does not contain the expected element with data-testid"""
    expect(page.get_by_test_id(data_testid)).not_to_be_visible()


@then(parsers.cfparse('I should see the text "{text}"'))
@then(parsers.cfparse('I should see the "{text}" message'))
def should_see_text(page: Page, text: str):
    """Checks the page for the expected text"""
    expect(page.get_by_text(text)).to_be_visible()


@then(parsers.cfparse('I should not see the text "{text}"'))
@then(parsers.cfparse('I should not see the "{text}" message'))
def should_not_see_text(page: Page, text: str):
    """Checks the page to make sure the expected text is not visible"""
    expect(page.get_by_text(text)).not_to_be_visible()


@then(parsers.cfparse("the {data_testid} should contain the text: {text}"))
@then(parsers.cfparse("{data_testid} should contain the text: {text}"))
def element_should_contain_text(data_testid: str, text: str, page: Page):
    """Checks the text of an element with the expected data-testid"""
    expect(page.get_by_test_id(data_testid)).to_have_text(text)


@then("I should see no console errors")
def should_see_no_console_errors(page: Page, console: ConsoleMessage):
    """
    Checks the console for any errors
    """
    errors = [msg.text for msg in console if msg.type == "error"]
    assert not errors, f"Console errors: {errors}"
