from lark import Token, Tree

from model_w.project_maker.template import parse_text


def test_parse_line():
    assert parse_text("foo\nbar\nbaz") == Tree(
        Token("RULE", "file"),
        [
            Tree(
                Token("RULE", "line"),
                [Tree(Token("RULE", "line_content"), [Token("TEXT", "foo")])],
            ),
            Tree(
                Token("RULE", "line"),
                [Tree(Token("RULE", "line_content"), [Token("TEXT", "bar")])],
            ),
            Tree(
                Token("RULE", "line"),
                [Tree(Token("RULE", "line_content"), [Token("TEXT", "baz")])],
            ),
        ],
    )
    assert parse_text("foo\nbar\nbaz\n") == Tree(
        Token("RULE", "file"),
        [
            Tree(
                Token("RULE", "line"),
                [Tree(Token("RULE", "line_content"), [Token("TEXT", "foo")])],
            ),
            Tree(
                Token("RULE", "line"),
                [Tree(Token("RULE", "line_content"), [Token("TEXT", "bar")])],
            ),
            Tree(
                Token("RULE", "line"),
                [Tree(Token("RULE", "line_content"), [Token("TEXT", "baz")])],
            ),
        ],
    )

    assert parse_text("foo") == Tree(
        Token("RULE", "file"),
        [
            Tree(
                Token("RULE", "line"),
                [Tree(Token("RULE", "line_content"), [Token("TEXT", "foo")])],
            ),
        ],
    )


def test_parse_reference():
    assert parse_text("___foo___\n") == Tree(
        Token("RULE", "file"),
        [
            Tree(
                Token("RULE", "line"),
                [
                    Tree(
                        Token("RULE", "line_content"),
                        [
                            Tree(
                                Token("RULE", "inline_ref"),
                                [
                                    Token("REF_DELIM", "___"),
                                    Tree(
                                        Token("RULE", "reference"),
                                        [Token("KEY", "foo")],
                                    ),
                                    Token("REF_DELIM", "___"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    assert parse_text("___foo_bar__baz___\n") == Tree(
        Token("RULE", "file"),
        [
            Tree(
                Token("RULE", "line"),
                [
                    Tree(
                        Token("RULE", "line_content"),
                        [
                            Tree(
                                Token("RULE", "inline_ref"),
                                [
                                    Token("REF_DELIM", "___"),
                                    Tree(
                                        Token("RULE", "reference"),
                                        [
                                            Token("KEY", "foo_bar"),
                                            Token("KEY", "baz"),
                                        ],
                                    ),
                                    Token("REF_DELIM", "___"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    assert parse_text("___foo__bar__baz___\n") == Tree(
        Token("RULE", "file"),
        [
            Tree(
                Token("RULE", "line"),
                [
                    Tree(
                        Token("RULE", "line_content"),
                        [
                            Tree(
                                Token("RULE", "inline_ref"),
                                [
                                    Token("REF_DELIM", "___"),
                                    Tree(
                                        Token("RULE", "reference"),
                                        [
                                            Token("KEY", "foo"),
                                            Token("KEY", "bar"),
                                            Token("KEY", "baz"),
                                        ],
                                    ),
                                    Token("REF_DELIM", "___"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_parse_mixed():
    assert (
        parse_text(
            """#!/usr/bin/python

import foo
import bar
import ___project__name___

___project__name___

my_thing = "___project__NAME___" 
    """
        )
        == Tree(
            Token("RULE", "file"),
            [
                Tree(
                    Token("RULE", "line"),
                    [
                        Tree(
                            Token("RULE", "line_content"),
                            [Token("TEXT", "#!/usr/bin/python")],
                        )
                    ],
                ),
                Tree(Token("RULE", "line"), []),
                Tree(
                    Token("RULE", "line"),
                    [
                        Tree(
                            Token("RULE", "line_content"),
                            [
                                Token("TEXT", "import foo"),
                            ],
                        )
                    ],
                ),
                Tree(
                    Token("RULE", "line"),
                    [
                        Tree(
                            Token("RULE", "line_content"),
                            [
                                Token("TEXT", "import bar"),
                            ],
                        )
                    ],
                ),
                Tree(
                    Token("RULE", "line"),
                    [
                        Tree(
                            Token("RULE", "line_content"),
                            [
                                Token("TEXT", "import "),
                            ],
                        ),
                        Tree(
                            Token("RULE", "line_content"),
                            [
                                Tree(
                                    Token("RULE", "inline_ref"),
                                    [
                                        Token("REF_DELIM", "___"),
                                        Tree(
                                            Token("RULE", "reference"),
                                            [
                                                Token("KEY", "project"),
                                                Token("KEY", "name"),
                                            ],
                                        ),
                                        Token("REF_DELIM", "___"),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
                Tree(Token("RULE", "line"), []),
                Tree(
                    Token("RULE", "line"),
                    [
                        Tree(
                            Token("RULE", "line_content"),
                            [
                                Tree(
                                    Token("RULE", "inline_ref"),
                                    [
                                        Token("REF_DELIM", "___"),
                                        Tree(
                                            Token("RULE", "reference"),
                                            [
                                                Token("KEY", "project"),
                                                Token("KEY", "name"),
                                            ],
                                        ),
                                        Token("REF_DELIM", "___"),
                                    ],
                                )
                            ],
                        )
                    ],
                ),
                Tree(Token("RULE", "line"), []),
                Tree(
                    Token("RULE", "line"),
                    [
                        Tree(Token("RULE", "line_content"), [Token("TEXT", "my")]),
                        Tree(Token("RULE", "line_content"), [Token("TEXT", "_")]),
                        Tree(
                            Token("RULE", "line_content"), [Token("TEXT", 'thing = "')]
                        ),
                        Tree(
                            Token("RULE", "line_content"),
                            [
                                Tree(
                                    Token("RULE", "inline_ref"),
                                    [
                                        Token("REF_DELIM", "___"),
                                        Tree(
                                            Token("RULE", "reference"),
                                            [
                                                Token("KEY", "project"),
                                                Token("KEY", "NAME"),
                                            ],
                                        ),
                                        Token("REF_DELIM", "___"),
                                    ],
                                )
                            ],
                        ),
                        Tree(Token("RULE", "line_content"), [Token("TEXT", '" ')]),
                    ],
                ),
                Tree(
                    Token("RULE", "line"),
                    [Tree(Token("RULE", "line_content"), [Token("TEXT", "    ")])],
                ),
            ],
        )
    )

def test_filter():
    pass
