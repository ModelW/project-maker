"""
These are the common then steps that can be used in scenarios.

- Then steps represent the assertions

Note: Different matchers can be used for the same step, to allow for more
      flexibility in the scenarios.  ie. to make the english make more sense.
      Be aware, the first matcher that matches will be used, so be careful if
      you have multiple matchers that could match the same step.
      When in doubt, play it simple and keep matchers unique to the step.
      ie. I should see the element "{data_testid}", and I should see the text
      "{data_testid}".
"""

import re
from collections.abc import Callable
from http import HTTPStatus
from io import BytesIO

import httpx
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image
from playwright.sync_api import (
    APIResponse,
    ConsoleMessage,
    Page,
    Playwright,
    Request,
    expect,
)
from pytest_bdd import parsers, then
from pytest_django.live_server_helper import LiveServer

from bdd.fixtures import Reporter
from bdd.report import utils as report_utils

from . import common_given, utils


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

    assert actual_colour == colour, (
        f"Actual colour: {actual_colour}, Expected colour: {colour}"
    )


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


# The data-testid can't end with a colon, which introduces the datatable or the
# docstring of steps such as "I should see the following Django admin models:"
@then(parsers.re(r'^I should see (?P<data_testid>[^"\n]*[^"\n:])$'))
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


@then(parsers.re(r'^I should not see (?P<data_testid>[^"\n]*[^"\n:])$'))
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


@then(parsers.cfparse('the page title should be "{text}"'))
@then(parsers.cfparse('I should see the page title as "{text}"'))
def should_see_page_title(page: Page, text: str):
    """Check the page title."""
    expect(page).to_have_title(text)


@then("there should be no console errors")
def should_be_no_console_errors(page: Page, console: ConsoleMessage):
    """Check the console for any errors."""
    errors = [msg.text for msg in console if msg.type == "error"]
    assert not errors, f"Console errors: {errors}"


@then("I should see the following Django admin models:")
def should_see_admin_models(page: Page, datatable: list[list[str]]):
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
    for row in utils.parse_datatable(datatable):
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


# :: IF api__wagtail
@then("the userbar should be shown")
def userbar_should_be_shown(page: Page):
    """Check the page for the expected userbar."""
    wagtail_userbar = page.get_by_role("button", name="View Wagtail quick actions")
    expect(wagtail_userbar).to_be_visible()


@then("the userbar should not be shown")
def userbar_should_not_be_shown(page: Page):
    """Check the page to make sure the expected userbar is not visible."""
    wagtail_userbar = page.get_by_role("button", name="View Wagtail quick actions")
    expect(wagtail_userbar).not_to_be_visible()


# :: ENDIF


@then("the following devices should not have any a11y violations:")
def should_not_have_any_a11y_violations(
    datatable: list[list[str]],
    page: Page,
    report: Reporter,
    playwright: Playwright,
):
    """
    Change the viewport size to the specified device, and check the page has no
    a11y violations.

    Example:
    ```gherkin
        Then the following devices should not have any a11y violations:
            | device         |
            | Desktop Chrome |
            | iPad (gen 7)   |
            | iPhone X       |
    ```
    """
    page.add_script_tag(url="https://unpkg.com/axe-core@4.8.3/axe.min.js")

    info = []
    violations = set()

    for row in utils.parse_datatable(datatable):
        info.append(f"<strong>{row['device']}</strong>")

        common_given.on_device(row["device"], page, playwright)

        results = page.evaluate(
            """
            axe.run({
                runOnly: {
                    type: 'tag',
                    values: ['wcag2a', 'wcag2aa']
                },
                absolutePaths: true
            })
            """,
        )

        if results["violations"]:
            [violations.add(violation["id"]) for violation in results["violations"]]
            info.append(report_utils.generate_a11y_report(results))
            info.append("<hr>")

    if violations:
        report.attach("<hr>".join(info), mime_type="text/html")

    assert not violations, f"Accessibility violations found: {violations}"


@then(
    parsers.cfparse(
        "the current page ({snapshot_name}) should not have any visual regressions",
    ),
)
def should_not_have_any_visual_regressions(
    snapshot_name: str,
    page: Page,
    front_server: str,
    assert_snapshot: Callable[[bytes, str, float], Image.Image | None],
    report: Reporter,
):
    """
    Verify that the visual snapshot of the current page remains unchanged.

    Snapshots are stored in the `snapshots` folder and named in the format:
    `<snapshot_name>.png`.

    Example:
    ```gherkin
        Then the current page (home) should not have any visual regressions
    ```
    """
    width, height = page.viewport_size["width"], page.viewport_size["height"]
    screenshot_name = f"{slugify(snapshot_name)}-{width}x{height}.png"

    # Disable transitions globally
    page.add_style_tag(
        content="* { transition: none !important; animation: none !important; }",
    )

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)  # Brief pause to reduce flakiness in screenshots

    # Scroll down to trigger any scroll-triggered animations
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)  # Wait for the animations to trigger

    # Scroll back up
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)  # Wait for the animations to complete

    difference: Image.Image | None = assert_snapshot(
        image_data=page.screenshot(full_page=True, type="png"),
        name=screenshot_name,
    )

    if difference:
        buffer = BytesIO()
        difference.save(buffer, format="PNG")
        report.attach_image(buffer.getvalue())

    assert difference is None, f"Screenshots are different: {screenshot_name}"


@then(parsers.cfparse('I should see the "{name}" {role} in the {region}'))
def should_see_role_in_region(name: str, role: str, region: str, page: Page):
    """
    Check that an element of the given role and accessible name is visible in
    a region of the page (see `utils.get_region()`).

    Example:
    ```gherkin
        Then I should see the "The team" link in the main navigation
        Then I should see the "Open the menu" button in the site header
    ```
    """
    region_locator = utils.get_region(page, region)
    element = region_locator.get_by_role(role, name=name, exact=True)
    expect(element).to_be_visible()


@then(parsers.cfparse('I should not see the "{name}" {role} in the {region}'))
def should_not_see_role_in_region(name: str, role: str, region: str, page: Page):
    """
    Check that no element of the given role and accessible name is visible in
    a region of the page.

    Example:
    ```gherkin
        Then I should not see the "The team" link in the main navigation
    ```
    """
    region_locator = utils.get_region(page, region)
    element = region_locator.get_by_role(role, name=name, exact=True)
    expect(element).not_to_be_visible()


@then(parsers.cfparse('the "{name}" {role} in the {region} should be {state}'))
def role_in_region_should_be(
    name: str,
    role: str,
    region: str,
    state: str,
    page: Page,
):
    """
    Check the state of an element: "focused", or "expanded" / "collapsed" for
    the buttons controlling a disclosure (through `aria-expanded`).

    Example:
    ```gherkin
        Then the "About" button in the main navigation should be expanded
        Then the "Skip to content" link in the page should be focused
    ```
    """
    region_locator = utils.get_region(page, region)
    element = region_locator.get_by_role(role, name=name, exact=True)

    if state == "focused":
        expect(element).to_be_focused()
    elif state in ("expanded", "collapsed"):
        expanded = "true" if state == "expanded" else "false"
        expect(element).to_have_attribute("aria-expanded", expanded)
    else:
        msg = f"Unknown state '{state}', use focused, expanded or collapsed"
        raise ValueError(msg)


@then(parsers.cfparse("the {region} should have the following links:"))
def region_should_have_links(region: str, page: Page, datatable: list[list[str]]):
    """
    Check that a region of the page shows the given links.

    Example:
    ```gherkin
        Then the main navigation should have the following links:
            | link |
            | Home |
    ```
    """
    region_locator = utils.get_region(page, region)

    for row in utils.parse_datatable(datatable):
        link = region_locator.get_by_role("link", name=row["link"], exact=True)
        expect(link).to_be_visible()


@then(parsers.cfparse("the {region} should have the following columns:"))
def region_should_have_columns(region: str, page: Page, datatable: list[list[str]]):
    """
    Check that a region of the page has columns titled by a heading, each one
    with a list of links named after that heading.

    Example:
    ```gherkin
        Then the site footer should have the following columns:
            | column         | link         |
            | Administration | Django admin |
    ```
    """
    region_locator = utils.get_region(page, region)

    for row in utils.parse_datatable(datatable):
        heading = region_locator.get_by_role("heading", level=2, name=row["column"])
        expect(heading).to_be_visible()

        column = region_locator.get_by_role("list", name=row["column"], exact=True)
        link = column.get_by_role("link", name=row["link"], exact=True)
        expect(link).to_be_visible()


@then(parsers.cfparse('I should see the level {level:d} heading "{name}"'))
def should_see_heading(level: int, name: str, page: Page):
    """
    Check the page for a heading of the given level and text.

    Example:
    ```gherkin
        Then I should see the level 1 heading "Demo Page"
    ```
    """
    heading = page.get_by_role("heading", level=level, name=name, exact=True)
    expect(heading).to_be_visible()


@then(
    parsers.cfparse('I should see the level {level:d} heading starting with "{start}"'),
)
def should_see_heading_starting_with(level: int, start: str, page: Page):
    """
    Check the page for a heading of the given level, starting with the text.

    Example:
    ```gherkin
        Then I should see the level 1 heading starting with "Welcome to"
    ```
    """
    name = re.compile(f"^{re.escape(start)}")
    expect(page.get_by_role("heading", level=level, name=name)).to_be_visible()


@then(parsers.cfparse('the page should not have requested "{path}"'))
def should_not_have_requested(path: str, network_requests: list[Request]):
    """
    Check that the browser made no request to the given path since the
    beginning of the scenario (on any host).

    Example:
    ```gherkin
        Then the page should not have requested "/back/api/me/"
    ```
    """
    requested = [
        request.url
        for request in network_requests
        if httpx.URL(request.url).path == path
    ]
    assert not requested, f"Unexpected requests: {requested}"


@then(parsers.cfparse('the body should use the "{custom_property}" font stack'))
def body_should_use_font_stack(custom_property: str, page: Page):
    """
    Check that the text of the page uses the font stack of a CSS custom property
    (compared once resolved, so the stack itself can change).

    Example:
    ```gherkin
        Then the body should use the "--font-body" font stack
    ```
    """
    expected, actual = page.evaluate(
        """(property) => [
            getComputedStyle(document.documentElement).getPropertyValue(property),
            getComputedStyle(document.body).fontFamily,
        ]""",
        custom_property,
    )

    assert expected.strip(), f"{custom_property} is not defined"
    assert actual == expected.strip(), f"Body font: {actual}, expected: {expected}"


@then("the CSS reset should be applied")
def css_reset_should_be_applied(page: Page):
    """Check that the reset of the global styles is loaded."""
    margin = page.evaluate("getComputedStyle(document.body).margin")
    assert margin == "0px", f"The body has a margin of {margin}"


@then("the main area should fill the screen below the site header")
def main_should_fill_screen_below_header(page: Page):
    """
    Check that the content starts below the fixed header and is at least as
    tall as the screen (so that the footer doesn't float mid-page).
    """
    header_box = page.get_by_role("banner").bounding_box()
    padding_top, height = page.get_by_role("main").evaluate(
        """(main) => [
            parseFloat(getComputedStyle(main).paddingTop),
            main.getBoundingClientRect().height,
        ]""",
    )

    assert header_box, "The site header is not displayed"
    assert padding_top == header_box["height"], (
        f"Main padding: {padding_top}px, header height: {header_box['height']}px"
    )
    assert height >= page.viewport_size["height"], f"Main is {height}px tall"


def get_site_header_height(page: Page) -> float:
    """Height of the fixed site header, in pixels (0 if it's not displayed)."""
    box = page.get_by_role("banner").bounding_box()
    return box["height"] if box else 0


@then(parsers.cfparse("the site header should be {height:d}px high"))
def site_header_should_be_high(height: int, page: Page):
    """
    Check the height of the fixed site header.

    Example:
    ```gherkin
        Then the site header should be 80px high
    ```
    """
    utils.wait_until(
        lambda: get_site_header_height(page) == height,
        lambda: f"The site header is {get_site_header_height(page)}px high",
    )


@then(parsers.cfparse("the site header should be less than {height:d}px high"))
def site_header_should_be_less_high(height: int, page: Page):
    """
    Check that the fixed site header has shrunk below a height, as it does
    when the page scrolls (with a CSS animation, hence the wait).

    Example:
    ```gherkin
        Then the site header should be less than 80px high
    ```
    """
    utils.wait_until(
        lambda: get_site_header_height(page) < height,
        lambda: f"The site header is still {get_site_header_height(page)}px high",
    )


@then("nothing should overflow the width of the screen")
def page_should_not_scroll_horizontally(page: Page):
    """Check that nothing overflows the width of the screen."""
    scroll_width, client_width = page.evaluate(
        """() => [
            document.documentElement.scrollWidth,
            document.documentElement.clientWidth,
        ]""",
    )

    assert scroll_width <= client_width, (
        f"The page is {scroll_width}px wide for a {client_width}px screen"
    )


@then(parsers.cfparse("the {region} should not scroll horizontally"))
def region_should_not_scroll_horizontally(region: str, page: Page):
    """
    Check that a region of the page can't be scrolled sideways by the visitor,
    even if some of its decoration overflows it (it must be clipped).

    Example:
    ```gherkin
        Then the mobile menu should not scroll horizontally
    ```
    """
    element = utils.get_region(page, region)
    viewport_width = page.viewport_size["width"]

    def is_within_screen() -> bool:
        box = element.bounding_box()
        return bool(box) and box["x"] >= 0 and box["x"] + box["width"] <= viewport_width

    # Drawers and the like may still be sliding in
    utils.wait_until(
        is_within_screen,
        lambda: f"The {region} is out of the screen: {element.bounding_box()}",
    )
    box = element.bounding_box()

    overflow_x = element.evaluate("(element) => getComputedStyle(element).overflowX")
    assert overflow_x in ("hidden", "clip"), (
        f"The {region} doesn't clip its overflow (overflow-x: {overflow_x})"
    )

    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.wheel(box["width"], 0)
    page.wait_for_timeout(300)  # Leaves time to the scroll, if any
    scroll_left = element.evaluate("(element) => element.scrollLeft")
    assert scroll_left == 0, f"The {region} scrolled {scroll_left}px sideways"


@then(
    parsers.cfparse(
        'I should see the level {level:d} heading "{name}" in the {preview} preview',
    ),
)
def should_see_heading_in_cms_preview(
    level: int,
    name: str,
    preview: str,
    page: Page,
):
    """
    Check the heading displayed by a preview panel of the Wagtail admin.

    Example:
    ```gherkin
        Then I should see the level 1 heading "Demo Page" in the page preview
    ```
    """
    frame = utils.get_cms_preview(page, preview)
    heading = frame.get_by_role("heading", level=level, name=name, exact=True)
    expect(heading).to_be_visible()


@then(
    parsers.cfparse(
        'I should be redirected to "{login_path}", to come back to "{path}"',
    ),
)
def should_be_redirected_to_login(
    login_path: str,
    path: str,
    response: APIResponse,
):
    """
    Check that the response (see "I request ... without following redirects")
    is a temporary redirection to a login page, which then sends back to the
    requested path through its `next` parameter.

    Example:
    ```gherkin
        Then I should be redirected to "/back/login/", to come back to "/me"
    ```
    """
    assert response.status == HTTPStatus.TEMPORARY_REDIRECT, (
        f"Got a {response.status} instead of a temporary redirection"
    )

    location = httpx.URL(response.headers["location"])
    assert location.path == login_path, f"Redirected to {location}"
    assert location.params.get("next") == path, (
        f"The login sends back to {location.params.get('next')} instead of {path}"
    )
