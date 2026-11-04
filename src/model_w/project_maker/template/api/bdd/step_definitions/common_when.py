"""
These are the common when steps that can be used in scenarios.

- When steps represent the actions steps

Note: Multiple regex patterns can be used on the same step, to make
      the feature files easier to read.
"""

import httpx
from playwright.sync_api import APIResponse, Page
from pytest_bdd import parsers, when

# :: IF api__testing
from ___project_name__snake___.apps.cms import models as cms_models

# :: ENDIF
from . import utils
from .common_given import at_url, on_page


@when(parsers.cfparse('I go to the URL "{url}"'))
def go_to_url(url: str, page: Page, front_server, live_server):
    """
    Navigates to the given URL, relative to the front-end server

    Example:
        When I go to the URL "/about"
    """
    at_url(url, page, front_server, live_server)


@when(parsers.cfparse("I visit the {page_name} page"))
def visit_page(page_name: str, page: Page, front_server):
    """
    Navigates to the page with the given name

    Example:
        When I visit the home page
    """
    on_page(page_name, page, front_server)


@when(parsers.cfparse("I click {data_testid}"))
@when(parsers.cfparse("I click the {data_testid} button"))
@when(parsers.cfparse("I click the {data_testid} link"))
def click_on_data_testid(data_testid: str, page: Page):
    """
    Clicks the element with the data-testid attribute

    Example:
        When I click show more videos
        When I click the submit button
        When I click the my bookings link

        <button data-testid="show more videos">...
        <button data-testid="submit">...
        <a data-testid="my bookings">...
    """
    page.get_by_test_id(data_testid).click()


@when(parsers.cfparse('I enter "{value}" in {data_testid}'))
def fill_data_testid_with_value(data_testid: str, value: str, page: Page):
    """
    Enters the value into the input with the data-testid attribute

    Example:
        When I enter "chicken" in favourite sandwich

        <input data-testid="favourite sandwich" />
    """
    page.get_by_test_id(data_testid).fill(value)


@when(parsers.cfparse('I {data_testid} for "{value}"'))
def search_data_testid_for(data_testid: str, value: str, page: Page):
    """
    Enters the value into the input with the data-testid attribute
    and presses the enter key

    Example:
        When I search users for "John Doe"
        When I search cities for "New York"

        <input data-testid="search users" />
        <input data-testid="search cities" />
    """
    page.get_by_test_id(data_testid).fill(value)
    page.keyboard.press("Enter")


@when("I submit the form with the following data:")
def fill_in_form_with_data(page: Page, datatable: list[list[str]]):
    """
    Fills in the form with the data provided.

    Example:
        When I submit the form with the following data:
        | age  | 25       |
        | name | John Doe |
        | city | New York |

    <input data-testid="age" />
    <input data-testid="name" />
    <input data-testid="city" />
    <button data-testid="submit" />
    """
    data = utils.parse_vertical_datatable(datatable)
    for key, value in data.items():
        page.get_by_test_id(key).fill(value)
    page.get_by_test_id("submit").click()


@when(parsers.cfparse("I log in with {username} and {password}"))
def log_in_with_username_and_password(username: str, password: str, page: Page):
    """
    Logs in with the username and password provided

    Example:
        When I log in with admin and password
    """
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)

    input_submit = page.locator('input[type="submit"]')
    button_submit = page.locator('button[type="submit"]')

    if input_submit.is_visible():
        input_submit.click()
    else:
        button_submit.click()


@when(parsers.cfparse('I press the "{name}" {role} in the {region}'))
def press_role_in_region(name: str, role: str, region: str, page: Page):
    """
    Clicks the element of the given role and accessible name, inside a region
    of the page (see `utils.get_region()`).

    Example:
        When I press the "About" button in the main navigation
        When I press the "Django admin" link in the site footer
    """
    # Clicks are lost if they happen before the page is hydrated
    page.wait_for_load_state("networkidle")
    utils.get_region(page, region).get_by_role(role, name=name, exact=True).click()


@when(parsers.cfparse("I press the {key} key"))
def press_key(key: str, page: Page):
    """
    Presses a key of the keyboard, named as Playwright names them.

    Example:
        When I press the Escape key
        When I press the Tab key
    """
    page.keyboard.press(key)


@when("I press an empty spot of the page")
def press_empty_spot(page: Page):
    """Clicks on the main area of the page, away from any menu or link."""
    page.get_by_role("main").click(position={"x": 1, "y": 200})


@when(parsers.cfparse("I scroll down by {pixels:d} pixels"))
def scroll_down(pixels: int, page: Page):
    """
    Scrolls the page down from its current position.

    Example:
        When I scroll down by 150 pixels
    """
    page.mouse.wheel(0, pixels)
    page.wait_for_function("y => window.scrollY >= y", arg=pixels)


@when(
    parsers.cfparse('I request "{path}" without following redirects'),
    target_fixture="response",
)
def request_without_redirects(
    path: str,
    page: Page,
    front_server: str,
) -> APIResponse:
    """
    Requests a page from the front with the browser's cookies, without
    following redirections, so that the response itself can be checked.

    Example:
        When I request "/__block_preview__" without following redirects
    """
    url = httpx.URL(front_server).join(path)
    return page.request.get(str(url), max_redirects=0)


# :: IF api__testing
@when("I open the demo page in the CMS editor")
def open_demo_page_in_editor(
    demo_page: cms_models.DemoPage,
    page: Page,
    front_server: str,
):
    """Opens the editor of the demo page in the Wagtail admin."""
    on_page(f"back/___cms_prefix___/pages/{demo_page.pk}/edit/", page, front_server)


@when("I open the demo snippet in the CMS editor")
def open_demo_snippet_in_editor(
    demo_snippet: cms_models.DemoSnippet,
    page: Page,
    front_server: str,
):
    """Opens the editor of the demo snippet in the Wagtail admin."""
    on_page(
        f"back/___cms_prefix___/snippets/cms/demosnippet/edit/{demo_snippet.pk}/",
        page,
        front_server,
    )


# :: ENDIF


# :: IF api__wagtail
@when("I toggle the CMS preview")
def toggle_cms_preview(page: Page):
    """Opens (or closes) the preview panel of a Wagtail editor."""
    page.get_by_role("button", name="Toggle preview").click()


@when(parsers.cfparse('I preview the "{block}" block from the block chooser'))
def preview_block_from_chooser(block: str, page: Page):
    """
    Opens the block chooser of the last StreamField of a Wagtail editor, then
    the preview of one of its blocks.

    Example:
        When I preview the "DemoBlock" block from the block chooser
    """
    page.get_by_role("button", name="Insert a block").last.click()

    # Each option of the chooser has its own preview button, next to it
    page.locator(".w-combobox__option-row").filter(
        has=page.get_by_role("option", name=block, exact=True),
    ).get_by_role("button", name="Preview", exact=True).click()


# :: ENDIF
