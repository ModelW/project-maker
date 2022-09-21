from pathlib import Path

from lark import Lark

with open(Path(__file__).parent / "grammar.lark") as f:
    grammar = Lark(f.read(), start="file", parser="lalr")


def parse_text(txt: str):
    return grammar.parse(txt)
