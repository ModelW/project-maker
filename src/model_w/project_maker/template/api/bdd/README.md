# BDD Testing

Here is where all the BDD testing for the entire project exists.

## Folder structure

-   [features](./features/) - the executable test files.
-   [step_definitions](./step_definitions/) - the code the feature files will
    run.
-   [fixtures](./fixtures/) - dependencies that can be used in any step
    definition.

## Installation

After installing the project, you will need to install the Playwright browsers
with: `playwright install` (Remember to have your virtual environment activated)

## How to use this BDD folder in a pre-existing ModelW project?

-   Copy this entire [bdd/](./) folder into /api of your ModelW project.
-   Copy the configs in [pyproject.toml](../pyproject.toml) for:
    -   `tool.poetry.group.test.dependencies`
    -   `tool.pytest.ini_options` (update settings location for your project)
-   `poetry lock --no-update` (to sync the new dependencies)
-   `poetry install` (to install the new dependencies)
-   `playwright install` (in your Poetry env)

## Quick start

The recipe for creating BDD tests is:

1. Create a feature file (using existing step definitions, if possible)
2. Create any missing step definitions
3. Add any missing data-testid attributes to elements in your source code
4. Run using `pytest`. (Use `--exitfirst` to fail immediately if one test fails)

Note: If you need to debug the site under test, run `PWDEBUG=1 pytest`, and you
can use Playwright's debugger.

To quicken the process while creating tests, you can skip the front's
`npm run build` stage with `SKIPBUILD=1 pytest`

Some reasonable defaults have been set in [pyproject.toml](../pyproject.toml),
however, any options can be set in the terminal when running pytest. See the
[docs](https://playwright.dev/python/docs/test-runners) for possible options, as
well as `pytest --help`.

## Usage

To run only certain tests, use `-m` and the list of tags to run (separated with
`and`). See the
[pytest-bdd docs](https://pytest-bdd.readthedocs.io/en/stable/#organizing-your-scenarios)
for info.

```bash
pytest -m current
```

This will run any tests decorated with that tag. You can decorate at both the
Feature, or Scenario level.

```gherkin
@current
Feature: ...

@current
Scenario: ...
```

### Skip the npm run build stage

To quicken the process while creating tests, when you know the front hasn't
changed,you can skip the front's `npm run build` stage with `SKIPBUILD=1 pytest`

### Target your front development server

Sometimes, it'e useful to target your front development server, rather than a
fresh one started by pytest (So you can see in real-time changes to the front /
front server logs live etc.). To do this, we need to set the live server's port
to be the same as your front is targeting and tell pytest to target your front's
dev server. For example, if your front is running on port 3000, and your api
server is running on port 8000, you can do the following:

-   Stop your dev api server
-   Run the following command:

```bash
SKIPBUILD=1 FRONTURL=http://localhost:3000 DJANGO_LIVE_TEST_SERVER_ADDRESS=localhost:8000 pytest
```

Furthermore, it's likely you have a specific test in mind you want to debug, so
a more realistic command might be:

```bash
PWDEBUG=1 SKIPBUILD=1 FRONTURL=http://localhost:3000 DJANGO_LIVE_TEST_SERVER_ADDRESS=localhost:8000 pytest -m current
```

Where, you're viewing the front in your browser, and just the test marked with
@current is running. You can then load localhost:3000 in your own browser and
see what the issue is, by watching your front server logs as normal.

### Run a specific test

If you want to run a specific test, you can use the `-k` flag to target a
specific test.

pytest

## Data creation

An important part of testing is having the right data to test on. Here, we can
take advantage of having Django as a test runner, and create data as we need it.

Data creation is going to be fairly project-specific, but generally speaking,
you will pick out the specific models that need to be created for your test and
create them in a [given](./step_definitions/common_given.py) step.

For example, `Given I am a manager in business` could be a step definition that
creates a business, fleet, a user with a manager role, and any other required
models.

Where creating data is fairly complex with many models requiring lots of other
models to work, we can use a tool like
[model-bakery](https://model-bakery.readthedocs.io/en/latest/) to automatically
create the data (including foreign relationship models). For example, if we are
testing a user with a profile type of manager, we need only specify the
following: `baker.make("user", profile__role="manager")`, and the associated
related models are automatically created, with any non-specified required fields
filled with random data. This also helps with maintenance, as updating models,
has less impact, than creating the test data manually.

### Data creation recipe

1. Identify the data necessary for the test
2. Create the data in a given step (`model-bakery` for easy creation)
3. Use the given step in feature files

## FAQ

-   Why is the BDD tests inside api/ as opposed to outside the site under test
    if it's acting on both frontend and backend?
    -   While slightly unconventional, having Django as the test runner for the
        E2E tests, means access to the DB to read or update at our convenience.
-   Why use `data-testid` attributes rather than CSS selectors?

    -   CSS classes need to be changeable by devs, but a fixed `data-testid`
        attribute lends itself to stability.

-   What value should I give the `data-testid` attribute?

    -   A good rule of thumb is something human-readable to look good in a
        feature file. Then, you can use it as a variable as is, ie.
        `When I click the {value} button` would look much better with
        `view books` rather than `view_books`, `viewBooks` or
        `input__view_books`.

-   Can I have duplicate `data-testid` values on a page?

    -   Short answer - yes, but don't. Longer answer - try and find a way to
        better describe the element on the page, eg.`view books (header)`. If it
        can't be avoided, then you can always target inside another
        `data-testid`. ie. `When I click the view books button in the header`.

-   Am I allowed to use technical steps like "click the button", as opposed to
    business domain language?

    -   Short answer - yes. Longer answer - Balance the need for quick test
        writing (reusing a small number of technical steps) vs strong
        communication (writing more specific business steps). My advice would be
        to start with the technical steps which are already written, so you can
        quickly create feature files, and then when you have more experience,
        start to encapsulate functionality into more business domain language.
        The ideal is to have purely business domain language in the feature
        file, so that it is completely immune from development changes. ie.
        `When I view my books` vs
        `When I click "account" And I click the "view-my-books" button`.

-   Should unit tests be BDD?

    -   While there's nothing stopping you from doing so, the scope of unit
        tests is too small to be particularly useful. The prevailing theory in
        the BDD world about unit tests is to simply name them starting with
        "should" and you'll almost have BDD there anywhere. eg.
        `"should_raise_error_with_empty_array"`.

-   Should integration tests be BDD?

    -   If it helps. Occasionally, it's useful to have communication with a PM
        if a particular API end point needs to behave strangely. But generally,
        as the scope is smaller, it's not so beneficial.

-   How do I write non-BDD unit tests?

    -   API: Simply make a file beginning with test\_ or ending with \_test, and
        write your test as pytest recommends. See [test_utils.py](test_utils.py)
        for an example.

    ```python
    # test_maths.py

    import math

    def test_pow():
        assert math.pow(2, 2) == 4.0
    ```

    See [Getting Started](https://docs.pytest.org/en/8.0.x/getting-started.html)
    for more examples.

## Official Documentation

### Playwright Python

[Documentation](https://playwright.dev/python/docs/intro)

[API Reference](https://playwright.dev/python/docs/api/class-playwright)

### Pytest-BDD

[Documentation](https://pytest-bdd.readthedocs.io/en/stable)

### Pytest-Django

[Documentation](https://pytest-django.readthedocs.io/en/latest)

### Pytest

[Documentation](https://docs.pytest.org/en/8.0.x)
