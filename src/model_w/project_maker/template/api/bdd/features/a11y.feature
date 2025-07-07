@a11y
Feature: Accessibility regression checks

    Scenario Outline: Pages should not have any a11y regressions
        Given I am on the <page name> page
        Then the following devices should not have any a11y violations:
            | device         |
            | Desktop Chrome |
            | iPad (gen 7)   |
            | iPhone X       |
        Examples:
            | page name |
            | non-cms   |
