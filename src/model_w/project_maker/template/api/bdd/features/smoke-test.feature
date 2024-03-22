@smoke
Feature: Smoke test for the site

    As a developer,
    I want to see the site working,
    So that I know the application is not down.

    Scenario: Shows correct Django admin page
        Given I am logged in as a Django admin
        Then I should see the text "welcome"
        And I should not see the text "log in"
        And I should be at the URL "http://localhost:3001/back/admin/"

    # :: IF api__wagtail
    Scenario: Shows correct wagtail page
        Given I am on the home page
        Then I should see the text "___project_name__natural_double_quoted___"
        And I should be at the URL "http://localhost:3001/"
        And I should see no console errors

    Scenario: Shows correct non wagtail page
        Given I am on the no-wagtail-index page
        Then I should see the text "Welcome to Model W"
        And I should see no console errors

    Scenario: Shows correct CMS admin page
        Given I am logged in as a CMS admin
        Then I should not see the text "Sign in to Wagtail"
        But I should see the text "Welcome to the ___project_name__natural_double_quoted___ Wagtail CMS"
        And I should be at a URL with "cms"

    Scenario: Shows Nuxt injected frontend on Wagtail content
        Given I am at the URL "<API_URL>"
        Then the text "___project_name__natural_double_quoted___" should be the colour "rgb(0, 0, 0)"
        When I go to the URL "<FRONT_URL>"
        Then the text "___project_name__natural_double_quoted___" should be the colour "rgb(255, 0, 0)"
        And I should see no console errors
# :: ENDIF

