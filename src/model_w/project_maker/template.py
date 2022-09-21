import re
from typing import Iterator, Mapping, NamedTuple, Optional, Sequence, TextIO

CONTROL_BLOCK_START = re.compile(r"^\s*(##|////)\s*")
INLINE_REF = re.compile(
    r"___(?P<ref>([a-zA-Z-])([a-zA-Z0-9-]|_(?!_))*(__([a-zA-Z-])([a-zA-Z0-9-]|_(?!_))*)*)___"
)
WS = re.compile(r"\s+")


class ParseError(ValueError):
    pass


class EndBlock(BaseException):
    def __init__(self, block: str):
        self.block = block


class Context:
    def __init__(self, data: Mapping):
        self.data = data

    def resolve(self, ref: "Ref"):
        try:
            ptr = self.data

            for x in ref.path:
                ptr = ptr[x]

            return ptr
        except KeyError:
            return None


class Ref(NamedTuple):
    path: Sequence[str]

    def execute(self, context: Context):
        out = context.resolve(self)

        if out is not None:
            return f"{out}"
        else:
            return ""


class Text(NamedTuple):
    text: str

    def execute(self, context: Context):
        return self.text


class IfBlock(NamedTuple):
    condition: Ref
    content: "File"

    def execute(self, context: Context):
        if context.resolve(self.condition):
            return self.content.execute(context)

        return ""


class Line(NamedTuple):
    content: Sequence[Text | Ref]

    def execute(self, context: Context):
        return "".join(x.execute(context) for x in self.content)


class File(NamedTuple):
    lines: Sequence[Line | IfBlock]

    def execute(self, context: Context):
        return "".join(x.execute(context) for x in self.lines)


class BlockLine(NamedTuple):
    cmd: str
    args: str = ""


def parse_line(line: str) -> Iterator[Text | Ref]:
    last_pos = 0

    for m in INLINE_REF.finditer(line):
        before = line[last_pos : m.start()]

        if before:
            yield Text(before)

        yield Ref(m.group("ref").split("__"))

        last_pos = m.end()

    end = line[last_pos:]

    if end:
        yield Text(end)


def parse_block(bl: BlockLine, text: TextIO) -> IfBlock:
    if bl.cmd != "IF":
        raise ParseError(f"Unexpected block line: {bl.cmd}")

    lines = []

    for line in text:
        try:
            lines.append(decompose_line(line, text))
        except EndBlock:
            return IfBlock(Ref(bl.args.split("__")), File(lines))


def detect_block_line(line: str) -> Optional[BlockLine]:
    if m := CONTROL_BLOCK_START.match(line):
        bl = BlockLine(*WS.split(line[m.end() :].strip(), 1))

        if bl.cmd == "IF":
            if not bl.args:
                raise ParseError("IF cannot be without condition")
        elif bl.cmd == "ENDIF":
            if bl.args:
                raise ParseError("Unexpected arguments after ENDIF")

        return bl


def decompose_line(line: str, text: TextIO) -> Line | IfBlock:
    if bl := detect_block_line(line):
        if bl.cmd == "ENDIF":
            raise EndBlock("IF")
        else:
            return parse_block(bl, text)
    else:
        return Line(list(parse_line(line)))


def parse_text(text: TextIO):
    lines = []

    for line in text:
        try:
            lines.append(decompose_line(line, text))
        except EndBlock:
            raise ParseError("Unexpected block end")

    return File(lines)
