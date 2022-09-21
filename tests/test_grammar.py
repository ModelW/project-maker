from io import StringIO

from model_w.project_maker.template import (
    Block,
    Context,
    IfBlock,
    Line,
    Ref,
    Text,
    parse_line,
    parse_text,
    render,
    render_line,
)


def test_parse_line():
    assert [*parse_line("foo")] == [Text("foo")]
    assert [*parse_line("___foo___")] == [Ref(["foo"])]
    assert [*parse_line("___foo__bar__baz___")] == [Ref(["foo", "bar", "baz"])]
    assert [*parse_line("hello ___foo___")] == [Text("hello "), Ref(["foo"])]
    assert [*parse_line("___foo___ stuff")] == [Ref(["foo"]), Text(" stuff")]
    assert [*parse_line("hello ___foo___ stuff")] == [
        Text("hello "),
        Ref(["foo"]),
        Text(" stuff"),
    ]


def test_parse_if():
    code = """## IF foo
yolo
## ENDIF
"""

    assert parse_text(StringIO(code)) == Block(
        lines=[
            IfBlock(
                condition=Ref(path=["foo"]),
                content=Block(lines=[Line(content=[Text(text="yolo\n")])]),
            )
        ]
    )

    code = """# Some code

from ___my_app___ import yolo

apps = [
    "foo",
    "bar",
    ## IF foo
    "baz"
    ## IF bar
    "bloop"
    ## ENDIF
    ## ENDIF
]
"""

    assert parse_text(StringIO(code)) == Block(
        lines=[
            Line(content=[Text(text="# Some code\n")]),
            Line(content=[Text(text="\n")]),
            Line(
                content=[
                    Text(text="from "),
                    Ref(path=["my_app"]),
                    Text(text=" import yolo\n"),
                ]
            ),
            Line(content=[Text(text="\n")]),
            Line(content=[Text(text="apps = [\n")]),
            Line(content=[Text(text='    "foo",\n')]),
            Line(content=[Text(text='    "bar",\n')]),
            IfBlock(
                condition=Ref(path=["foo"]),
                content=Block(
                    lines=[
                        Line(content=[Text(text='    "baz"\n')]),
                        IfBlock(
                            condition=Ref(path=["bar"]),
                            content=Block(
                                lines=[Line(content=[Text(text='    "bloop"\n')])]
                            ),
                        ),
                    ]
                ),
            ),
            Line(content=[Text(text="]\n")]),
        ]
    )


def test_execute():
    code = """# Some code

from ___my_app___ import yolo

apps = [
    "foo",
    "bar",
    ## IF foo__bar
    "baz",
    ## IF bar
    "bloop",
    ## ENDIF
    ## ENDIF
]
"""
    output = """# Some code

from yolo import yolo

apps = [
    "foo",
    "bar",
    "baz",
]
"""

    context = Context(
        {
            "my_app": "yolo",
            "foo": dict(bar=True),
        }
    )

    assert parse_text(StringIO(code)).execute(context) == output


def test_render():
    assert render("___foo___", dict(foo=42)) == "42"


def test_render_line():
    assert render_line("___foo___", dict(foo=42)) == "42"
