@smoke
Feature: Smoke test for the site

    As a developer,
    I want to see the site working,
    So that I know the application is not down.

    Scenario: Shows correct Django admin page
        Given I am logged in as a Django admin
        Then I should see the text "welcome"
        And I should not see the text "log in"
        And I should be at a URL with "back/admin/"
        And I should see the following Django admin models:
            | Group name                       | Model name         |
            | Authentication and Authorization | Groups             |
            | Procrastinate                    | Procrastinate jobs |
            # :: IF api__wagtail
            | Taggit                           | Tags               |
    # :: ENDIF

    Scenario: Non-admin user can't log in to Django admin
        Given I am the following user:
            | email    | good2@user.com |
            | is_admin | no             |
            | password | correct        |
        And I am on the /back/admin page
        When I log in with good2@user.com and correct
        Then I should see the text "Please enter the correct email address and password for a staff account"

    # :: IF front__enable
    Scenario: Shows the site layout
        Given I am on the home page
        Then I should see the "site header"
        And I should see the "site footer"
        And there should be no console errors
        # MW-166: the layout's landmarks, menus and global styles, appended to
        # this journey because it already lands on a public page with the full
        # layout, at a desktop width.
        And I should see the "___project_name__natural___ — Home" link in the site header
        And the main navigation should have the following links:
            | link    |
            | Home    |
            # :: IF api__testing
            | Demo    |
            # :: ENDIF
            # :: IF api__wagtail
            | Non-CMS |
            # :: ENDIF
        And the site footer should have the following columns:
            | column                      | link         |
            | ___project_name__natural___ | Home         |
            | Administration              | Django admin |
        And the body should use the "--font-body" font stack
        And the CSS reset should be applied
        And the main area should fill the screen below the site header
        When I press the Tab key
        Then the "Skip to content" link in the page should be focused
        # The About dropdown opens on click, then closes with Escape (giving
        # the focus back to its button) or when clicking elsewhere
        When I press the "About" button in the main navigation
        Then the "About" button in the main navigation should be expanded
        And I should see the "The project" link in the main navigation
        And I should see the "The team" link in the main navigation
        When I press the Escape key
        Then the "About" button in the main navigation should be collapsed
        And I should not see the "The project" link in the main navigation
        And the "About" button in the main navigation should be focused
        When I press the "About" button in the main navigation
        And I press an empty spot of the page
        Then the "About" button in the main navigation should be collapsed
        # The fixed header shrinks as the page scrolls
        And the site header should be 80px high
        When I scroll down by 150 pixels
        Then the site header should be less than 80px high
        # Public pages never fetch the session, not even after a client-side
        # navigation
        And the page should not have requested "/back/api/me/"
        # :: IF api__wagtail
        When I press the "Non-CMS" link in the main navigation
        Then I should see the level 1 heading starting with "Welcome to"
        And the page should not have requested "/back/api/me/"
        # :: ENDIF
        # Links to the back-end are full page loads, not front-end routes
        When I press the "Django admin" link in the site footer
        Then I should be at a URL with "back/admin/login/?next=/back/admin/"

    # MW-166: no existing scenario runs at a mobile width
    Scenario: Shows the mobile site layout
        Given I change screen size to that of a iPhone X
        And I am on the home page
        Then I should not see the "Main" navigation in the site header
        And I should see the "Open the menu" button in the site header
        When I press the "Open the menu" button in the site header
        Then I should see the "mobile menu"
        And nothing should overflow the width of the screen
        And the mobile menu should not scroll horizontally
        # Same-page links close the drawer too, giving the focus back to the
        # burger
        When I press the "About" button in the mobile menu
        And I press the "The project" link in the mobile menu
        Then I should not see the "mobile menu"
        And the "Open the menu" button in the site header should be focused
        And I should be at the URL "<FRONT_URL>/#project"
        And there should be no console errors
    # :: ENDIF

    # :: IF api__wagtail
    Scenario: Shows correct CMS admin page
        Given I am logged in as a CMS admin
        Then I should not see the text "Sign in to Wagtail"
        But I should see the page title as "Dashboard - Wagtail"
        And I should be at a URL with "___cms_prefix___"
    # :: ENDIF

    # :: IF api__wagtail
    # :: IF front__enable
    Scenario: Shows correct wagtail page
        Given I am on the home page
        Then I should see the text "___project_name__natural_double_quoted___"
        And I should be at the URL "<FRONT_URL>"
        And there should be no console errors

    @userbar
    Scenario: Shows Wagtail userbar when logged in
        Given I am logged in as a CMS admin
        When I go to the URL "<FRONT_URL>"
        Then the userbar should be shown

    @userbar
    Scenario: Hides Wagtail userbar when not logged in
        When I go to the URL "<FRONT_URL>"
        Then the userbar should not be shown

    @redirects
    Scenario: Redirects work correctly
        Given a permanent redirect exists from /redirect to /home
        When I visit the /redirect page
        Then I should be at the URL "<FRONT_URL>/home"

    # MW-166: previews are rendered by the front, for editors only
    @previews
    Scenario Outline: Anonymous visitors are sent to the CMS login from previews
        When I request "<path>" without following redirects
        Then I should be redirected to "/back/___cms_prefix___/login/", to come back to "<path>"

        Examples:
            | path                 |
            | /__block_preview__   |
            | /__snippet_preview__ |
            | /?in_preview_panel=1 |
    # :: ENDIF
    # :: ENDIF

    # :: IF api__testing
    @demopage
    Scenario: Shows correct Demo page
        Given I have created the demo page
        When I go to the URL "<FRONT_URL>/demo"
        Then there should be no console errors
        # MW-166: nested blocks (DemoBlock > DemoSubBlock > Heading) rendered
        # through the block registry, appended here because this journey
        # already lands on the demo page
        And I should see the level 1 heading "Demo Page"
        And I should see the level 3 heading "Demo block"
        And I should see the level 5 heading "Demo Sub Block"
        And I should see the text "Hydration status: true"

    # MW-166: no existing scenario opens the Wagtail editor
    @previews
    Scenario: Editor previews the demo page and one of its blocks
        Given I have created the demo page
        And I am logged in as a CMS admin
        When I open the demo page in the CMS editor
        And I toggle the CMS preview
        Then I should see the level 1 heading "Demo Page" in the page preview
        When I preview the "DemoBlock" block from the block chooser
        Then I should see the level 3 heading "Demo block" in the block preview

    @previews
    Scenario: Editor previews a demo snippet
        Given I have created a demo snippet titled "Tester snippet"
        And I am logged in as a CMS admin
        When I open the demo snippet in the CMS editor
        And I toggle the CMS preview
        Then I should see the level 1 heading "Tester snippet" in the snippet preview

# :: ENDIF
