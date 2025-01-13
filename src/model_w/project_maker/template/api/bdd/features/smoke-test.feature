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
            | Group name                       | Model name    |
            | Authentication and Authorization | Groups        |
            # :: IF api__celery
            | Celery Results                   | Group Results |
            | Celery Results                   | Task Results  |
            # :: ENDIF
            # :: IF api__wagtail
            | Taggit                           | Tags          |
    # :: ENDIF

    Scenario Outline: Needs correct log in to access Django admin
        Given I am on the /back/admin page
        When I log in with <username> and <password>
        Then I should see the text "<expected_text>"
        And I should not see the text "<not_expected_text>"

        Examples:
            | username      | password  | expected_text            | not_expected_text        |
            | good@user.com | correct   | welcome                  | Please enter the correct |
            | good@user.com | incorrect | Please enter the correct | welcome                  |
            | bad@user.com  | correct   | Please enter the correct | welcome                  |

    Scenario: Non-admin user can't log in to Django admin
        Given I am the following user:
            | email    | good2@user.com |
            | is_admin | no             |
            | password | correct        |
        And I am on the /back/admin page
        When I log in with good2@user.com and correct
        Then I should see the text "Please enter the correct email address and password for a staff account"

    # :: IF api__wagtail
    Scenario: Shows correct wagtail page
        Given I am on the home page
        Then I should see the text "___project_name__natural_double_quoted___"
        And I should be at the URL "<FRONT_URL>"
        And there should be no console errors

    Scenario: Shows correct CMS admin page
        Given I am logged in as a CMS admin
        Then I should not see the text "Sign in to Wagtail"
        But I should see the text "Welcome to the ___project_name__natural_double_quoted___"
        And I should be at a URL with "___cms_prefix___"

    Scenario: Shows injected frontend on Wagtail content
        When I go to the URL "<FRONT_URL>"
        Then the text "___project_name__natural_double_quoted___" should be the colour "rgb(255, 0, 0)"
        And there should be no console errors

    @redirects
    Scenario: Redirects work correctly
        Given a permanent redirect exists from /redirect to /home
        When I visit the /redirect page
        Then I should be at the URL "<FRONT_URL>/home"
    # :: ENDIF

    # :: IF api__testing
    @demopage
    Scenario: Shows correct Demo page
        Given I have created the demo page
        When I go to the URL "<FRONT_URL>/demo"
        Then there should be no console errors

# :: ENDIF
