"""
The setup wizard: its naming rules and options, then the TUI itself, driven
through Textual's pilot with a fake generation.
"""

import asyncio
from collections.abc import Mapping
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console
from textual.widgets import Button, Input, Static, Tree

from model_w.project_maker.namer import generate_declinations
from model_w.project_maker.wizard import WizardApp
from model_w.project_maker.wizard.options import (
    OVERRIDABLE,
    Options,
    check_admin_prefix,
    check_camel_low,
    check_camel_up,
    check_dashed,
    check_snake,
    check_snake_up,
)
from model_w.project_maker.wizard.picker import FolderPicker
from model_w.project_maker.wizard.progress import Outcome, ProgressScreen
from model_w.project_maker.words import random_slug

# --- Naming rules ---


@pytest.mark.parametrize("name", ["my_project", "pizza3000", "a_1_b"])
def test_valid_snake(name):
    assert check_snake(name) is None


@pytest.mark.parametrize(
    "name, error",
    [
        ("MyProject", "Lowercase"),
        ("2048_game", "starting with a letter"),
        ("double__underscore", "single underscores"),
        ("trailing_", "single underscores"),
        ("import", "keyword"),
        ("match", "keyword"),
        ("json", "standard library"),
        ("django", "already used"),
        ("bdd", "already used"),
        ("a" * 64, "63 characters"),
    ],
)
def test_invalid_snake(name, error):
    assert error in (check_snake(name) or "")


@pytest.mark.parametrize(
    "check, name, valid",
    [
        (check_snake_up, "MY_PROJECT", True),
        (check_snake_up, "MY__PROJECT", False),
        (check_snake_up, "my_project", False),
        (check_camel_low, "myProject", True),
        (check_camel_low, "v2_3Api", True),
        (check_camel_low, "MyProject", False),
        (check_camel_low, "my_project", False),
        (check_camel_up, "MyProject", True),
        (check_camel_up, "V2_3Api", True),
        (check_camel_up, "myProject", False),
        (check_camel_up, "My-Project", False),
    ],
)
def test_camel_and_upper_styles(check, name, valid):
    assert (check(name) is None) is valid


@pytest.mark.parametrize("name", ["my-project", "pizza-3000", "3d-shop"])
def test_valid_dashed(name):
    assert check_dashed(name) is None


@pytest.mark.parametrize("name", ["My-Project", "my_project", "a--b", "-a", ""])
def test_invalid_dashed(name):
    assert check_dashed(name)


@pytest.mark.parametrize(
    "prefix, valid",
    [
        ("quiet-otter", True),
        ("back_office", True),
        ("api", False),
        ("static", False),
        ("With Spaces", False),
        ("a/b", False),
    ],
)
def test_admin_prefix(prefix, valid):
    assert (check_admin_prefix(prefix) is None) is valid


def test_random_admin_prefix_is_valid():
    for _ in range(100):
        assert check_admin_prefix(random_slug()) is None


# --- Options ---


def test_names_derive_from_the_title(tmp_path):
    options = Options(title="Pizza Delivery 3000", parent=tmp_path)

    assert options.names["snake"] == "pizza_delivery_3000"
    assert options.names["dashed"] == "pizza-delivery-3000"
    assert options.target == tmp_path / "pizza-delivery-3000"
    assert options.errors() == {}


def test_overrides_replace_the_derived_names(tmp_path):
    overrides = {"snake": "pz", "dashed": "pz-web", "camel_up": "PZApp"}
    options = Options(title="Pizza", overrides=overrides, parent=tmp_path)

    assert options.names["snake"] == "pz"
    assert options.names["dashed"] == "pz-web"
    assert options.names["camel_up"] == "PZApp"
    # The others still derive from the title
    assert options.names["snake_up"] == "PIZZA"
    assert options.names["camel_low"] == "pizza"
    assert options.target == tmp_path / "pz-web"
    assert options.errors() == {}


@pytest.mark.parametrize(
    "key, value",
    [
        ("snake_up", "Pizza"),
        ("camel_low", "Pizza"),
        ("camel_low", "pizza_app"),
        ("camel_up", "pizzaApp"),
        ("camel_up", "Pizza-App"),
    ],
)
def test_each_declination_has_its_style(tmp_path, key, value):
    options = Options(title="Pizza", overrides={key: value}, parent=tmp_path)

    assert set(options.errors()) == {key}


@pytest.mark.parametrize(
    "title",
    ["Pizza Delivery 3000", "v2 3 api", "setIBAN number", "Élan Vital", "my-app"],
)
def test_derived_names_follow_their_own_style(title):
    """The wizard must accept whatever the namer derives (from a valid name)"""

    names = generate_declinations(title)

    for declination in OVERRIDABLE:
        assert declination.check(names[declination.key]) is None, declination.key


def test_underivable_name_asks_for_an_override(tmp_path):
    errors = Options(title="2048", parent=tmp_path).errors()

    assert "set it yourself" in errors["snake"]
    assert "dashed" not in errors


def test_snake_is_only_an_npm_name_without_api(tmp_path):
    assert "snake" not in Options(title="Json", api=False, parent=tmp_path).errors()
    assert "snake" in Options(title="Json", parent=tmp_path).errors()


def test_needs_a_component(tmp_path):
    errors = Options(title="x", front=False, api=False, parent=tmp_path).errors()

    assert "components" in errors


def test_target_must_be_new_or_empty(tmp_path):
    options = Options(title="Taken", parent=tmp_path)
    options.target.mkdir()

    assert options.errors() == {}

    (options.target / "file").touch()

    assert "isn't empty" in options.errors()["target"]


def test_children_need_their_parent(tmp_path):
    options = Options(
        title="x",
        api=False,
        wagtail=True,
        channels=True,
        demo_snippet=True,
        admin_prefix="api",
        parent=tmp_path,
    )
    context = options.context("Dev <dev@example.com>")

    assert not context["api"]["enable"]
    # Invalid, but irrelevant without Wagtail
    assert "admin_prefix" not in options.errors()


# --- The TUI ---


class FakeGeneration:
    """Records what the wizard asks to generate, instead of generating"""

    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: list[tuple[Path, Mapping]] = []

    def __call__(self, target, context, progress):
        self.calls.append((target, context))
        progress("Rendering the template")
        progress("Formatting with Prettier")

        if self.error:
            raise self.error


def run(scenario, tmp_path: Path, generate=None):
    """
    Runs the app headless and plays the scenario (an async function receiving
    the app and the pilot). Returns the app's return value.
    """

    app = WizardApp(
        dev_dir=tmp_path,
        dev_id="Dev <dev@example.com>",
        generate=generate or FakeGeneration(),
    )

    async def main():
        async with app.run_test(size=(160, 60)) as pilot:
            await scenario(app, pilot)

    asyncio.run(main())

    return app.return_value


async def set_value(app, pilot, selector: str, value) -> None:
    app.screen.query_one(selector).value = value
    await pilot.pause()


def text(app, selector: str) -> str:
    """Plain text of a Static of the current screen"""

    console = Console(width=200, record=True, file=StringIO())
    console.print(app.screen.query_one(selector, Static).content)
    return console.export_text()


def test_title_drives_the_derived_names_and_preview(tmp_path):
    async def scenario(app, pilot):
        await pilot.press(*"Pizza Delivery")
        await pilot.pause()

        assert app.query_one("#snake", Input).value == "pizza_delivery"
        assert app.query_one("#dashed", Input).value == "pizza-delivery"
        assert app.query_one("#snake", Input).disabled
        assert "pizza-delivery/" in str(app.query_one("#files", Tree).root.label)
        assert str(tmp_path / "pizza-delivery") in text(app, "#overview")
        assert not app.query_one("#create", Button).disabled

    run(scenario, tmp_path)


def test_children_are_greyed_out_without_their_parent(tmp_path):
    async def scenario(app, pilot):
        await set_value(app, pilot, "#admin_prefix", "quiet-otter")

        assert app.query_one("#demo_snippet").disabled
        assert "/back/quiet-otter/admin/" in text(app, "#overview")
        assert "/back/quiet-otter/cms/" not in text(app, "#overview")

        await pilot.click("#wagtail")
        await pilot.pause()

        assert not app.query_one("#demo_snippet").disabled
        assert "/back/quiet-otter/cms/" in text(app, "#overview")

        await pilot.click("#api")
        await pilot.pause()

        for id_ in ["admin_prefix", "shuffle", "wagtail", "channels", "demo_snippet"]:
            assert app.query_one(f"#{id_}").disabled

        assert "/back/quiet-otter/" not in text(app, "#overview")

    run(scenario, tmp_path)


def test_invalid_override_blocks_the_creation(tmp_path):
    async def scenario(app, pilot):
        await pilot.press(*"Pizza")
        await pilot.click("#snake-override")
        await pilot.pause()

        assert not app.query_one("#snake", Input).disabled

        await set_value(app, pilot, "#snake", "import")

        assert "keyword" in text(app, "#snake-error")
        assert app.query_one("#create", Button).disabled

        await set_value(app, pilot, "#snake", "pizza_app")

        assert app.query_one("#create", Button).disabled is False

    run(scenario, tmp_path)


def test_creates_with_the_chosen_options(tmp_path):
    generation = FakeGeneration()

    async def scenario(app, pilot):
        await pilot.press(*"Pizza")
        await pilot.click("#wagtail")
        await pilot.click("#dashed-override")
        await pilot.pause()
        await set_value(app, pilot, "#dashed", "pizza-web")
        await set_value(app, pilot, "#admin_prefix", "quiet-otter")
        await pilot.press("ctrl+g")
        await pilot.pause()

        assert isinstance(app.screen, ProgressScreen)

        await app.workers.wait_for_complete()
        await pilot.pause()

        assert "Formatting with Prettier" in text(app, "#progress-steps")
        assert "All clean and tidy" in text(app, "#progress-outcome")

        await pilot.click("#progress-done")
        await pilot.pause()

    outcome = run(scenario, tmp_path, generation)

    assert outcome == Outcome(tmp_path / "pizza-web")
    ((target, context),) = generation.calls
    assert target == tmp_path / "pizza-web"
    assert context["api"]["wagtail"]
    assert context["admin_prefix"] == "quiet-otter"
    assert context["project_name"]["snake"] == "pizza"


def test_shows_generation_errors(tmp_path):
    async def scenario(app, pilot):
        await pilot.press(*"Pizza")
        await pilot.press("ctrl+g")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert "something went wrong" in text(app, "#progress-outcome")
        assert "poetry exploded" in text(app, "#progress-error-text")

        await pilot.click("#progress-done")
        await pilot.pause()

    outcome = run(scenario, tmp_path, FakeGeneration(RuntimeError("poetry exploded")))

    assert not outcome.success


def test_shuffle_draws_another_admin_prefix(tmp_path):
    async def scenario(app, pilot):
        prefix_input = app.query_one("#admin_prefix", Input)
        seen = {prefix_input.value}

        for _ in range(5):
            await pilot.click("#shuffle")
            await pilot.pause()
            seen.add(prefix_input.value)

        # 4096 combinations, 6 draws: a collision on all of them is impossible
        assert len(seen) > 1
        assert all(check_admin_prefix(p) is None for p in seen)

    run(scenario, tmp_path)


def test_folder_picker_changes_the_location(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    async def scenario(app, pilot):
        await pilot.press(*"Pizza")
        await pilot.press("ctrl+o")
        await pilot.pause()

        assert isinstance(app.screen, FolderPicker)

        await set_value(app, pilot, "#picker-path", str(elsewhere))
        await pilot.click("#picker-select")
        await pilot.pause()

        assert not isinstance(app.screen, FolderPicker)
        assert str(elsewhere / "pizza") in text(app, "#overview")

    run(scenario, tmp_path)
