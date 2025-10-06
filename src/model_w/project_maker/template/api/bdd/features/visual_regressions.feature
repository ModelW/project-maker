@vr @skipCI
Feature: Visual regression checks

    As a developer,
    I want to check that the styling of pages has not been unintentially altered,
    So that I know my changes haven't had any unforseen side effects.

    Scenario Outline: Pages should not have any desktop visual regressions
        Given I change screen size to that of a Desktop Chrome
        When I visit the <page_name> page
        Then the current page (<page_name>) should not have any visual regressions

        Examples:
            | page_name |
            | non-cms   |


    Scenario Outline: Pages should not have any tablet visual regressions
        Given I change screen size to that of a iPad (gen 7)
        When I visit the <page_name> page
        Then the current page (<page_name>) should not have any visual regressions

        Examples:
            | page_name |
            | non-cms   |


    Scenario Outline: Pages should not have any mobile visual regressions
        Given I change screen size to that of a iPhone X
        When I visit the <page_name> page
        Then the current page (<page_name>) should not have any visual regressions

        Examples:
            | page_name |
            | non-cms   |

