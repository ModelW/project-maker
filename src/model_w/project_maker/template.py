import re
from io import StringIO
from typing import Iterator, Mapping, NamedTuple, Optional, Sequence, TextIO

CONTROL_BLOCK_START = re.compile(r"^\s*(#|//) ::\s*")
INLINE_REF = re.compile(
    r"___(?P<ref1>([a-zA-Z-])([a-zA-Z0-9-]|_(?!_))*((__|~~)([a-zA-Z-])([a-zA-Z0-9-]|_(?!_))*)*)___"
    r"|~~~(?P<ref2>([a-zA-Z-])([a-zA-Z0-9-]|_(?!_))*((__|~~)([a-zA-Z-])([a-zA-Z0-9-]|_(?!_))*)*)~~~"
)
WS = re.compile(r"\s+")
SEP = re.compile(r"__|~~")


class ParseError(ValueError):
    """
    Something went wrong during the parsing. Very unsophisticated exception for
    now!
    """


class EndBlock(BaseException):
    """
    An exception that isn't really an error but rather a tool to control the
    execution flow during parsing.
    """

    def __init__(self, block: str):
        self.block = block


class Context:
    def __init__(self, data: Mapping):
        self.data = data

    def resolve(self, ref: "Ref"):
        """
        Fetches a value from the data based on the key path from the Ref. For
        example Ref(['a', 'b', 'c']) points to self.data['a']['b']['c'].

        If the key isn't found, then we return None, as we try to be forgiving.
        """

        try:
            ptr = self.data

            for x in ref.path:
                ptr = ptr[x]

            return ptr
        except KeyError:
            return None


class Ref(NamedTuple):
    """
    A reference to the context
    """

    path: Sequence[str]

    def execute(self, context: Context):
        """
        We're getting the value from the context and rendering it to string,
        with a few things:

        - If the value doesn't resolve, we get None (cf context.resolve())
        - If we got None, we render as empty string (instead of rendering None)
        - Otherwise we just convert whatever value into a str
        """

        out = context.resolve(self)

        if out is not None:
            return f"{out}"
        else:
            return ""


class Text(NamedTuple):
    """
    A literal text block
    """

    text: str

    def execute(self, context: Context):
        return self.text


class IfBlock(NamedTuple):
    """
    A conditional block
    """

    condition: Ref
    content: "Block"

    def execute(self, context: Context) -> str:
        if context.resolve(self.condition):
            return self.content.execute(context)

        return ""


class Line(NamedTuple):
    """
    A parsed line
    """

    content: Sequence[Text | Ref]

    def execute(self, context: Context) -> str:
        return "".join(x.execute(context) for x in self.content)


class Block(NamedTuple):
    """
    A whole file or the content of a block
    """

    lines: Sequence[Line | IfBlock]

    def execute(self, context: Context) -> str:
        return "".join(x.execute(context) for x in self.lines)


class BlockLine(NamedTuple):
    """
    Parsed block control line
    """

    cmd: str
    args: str = ""


def parse_line(line: str) -> Iterator[Text | Ref]:
    """
    For a given line, goes around trying to find bits to be interpolated.
    The outcome is a list of tokens that are either raw text either references
    to the context that will be rendered later.

    Parameters
    ----------
    line
        A line to parse
    """

    last_pos = 0

    for m in INLINE_REF.finditer(line):
        before = line[last_pos : m.start()]

        if before:
            yield Text(before)

        yield Ref(SEP.split(m.group("ref1") or m.group("ref2")))

        last_pos = m.end()

    end = line[last_pos:]

    if end:
        yield Text(end)


def parse_block(bl: BlockLine, text: TextIO) -> IfBlock:
    """
    Parses a block until (that'll sound dumb) the end of block is reached by
    the decompose_line() function, in which case we know we're done with this
    block and and we can return.

    Parameters
    ----------
    bl
        Parsed block intro
    text
        Rest of the text
    """

    if bl.cmd != "IF":
        raise ParseError(f"Unexpected block line: {bl.cmd}")

    lines = []

    for line in text:
        try:
            lines.append(decompose_line(line, text))
        except EndBlock:
            return IfBlock(Ref(SEP.split(bl.args)), Block(lines))


def detect_block_line(line: str) -> Optional[BlockLine]:
    """
    If we're on a block line, let's try to detect the block's content and
    arguments. For now it's super simplistic.

    Parameters
    ----------
    line
        Line to be parsed
    """

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
    """
    We detect the kind of line that we're working on and do some sanity check:

    - If we're on an opening block, then we start parsing the block recursively
    - The way to end the execution of a block is with the EndBlock exception.
      Since we're sharing the same TextIO, when the parse_block() ends its
      execution all the relevant lines have been consumed and we can continue
      moving forward
    - Could also be a straightforward line

    Parameters
    ----------
    line
        Current line
    text
        Rest of the text
    """

    if bl := detect_block_line(line):
        if bl.cmd == "ENDIF":
            raise EndBlock("IF")
        else:
            return parse_block(bl, text)
    else:
        return Line(list(parse_line(line)))


def parse_text(text: TextIO) -> Block:
    """
    Entry function to transform the text into an AST. Then each node of the AST
    can be rendered using their execute() function.

    The core idea of this code template DSL is that we consider each line as
    either a "code" line, in which we'll inject the context but otherwise that
    will be rendered as-is, either as a control line that will open or close
    a control block (so far and probably forever just IF/ENDIF).

    A control block in itself is treated as a line, it's just that its
    execute() function will either return nothing either return its content
    based on the condition.

    Parameters
    ----------
    text
        Text to be parsed
    """

    lines = []

    for line in text:
        try:
            lines.append(decompose_line(line, text))
        except EndBlock:
            raise ParseError("Unexpected block end")

    return Block(lines)


def render(text: TextIO | str, context: Mapping | Context) -> str:
    """
    That's the easy way to render the code template. The provided text will
    be parsed then executed with the provided context.

    Parameters
    ----------
    text
        Code you want to render. If you provide a TextIO, it will be fully
        read at the end of the execution.
    context
        Context to be injected during rendering
    """

    if isinstance(text, str):
        text = StringIO(text)

    if not isinstance(context, Context):
        context = Context(context)

    return parse_text(text).execute(context)


def render_line(line: str, context: Mapping | Context) -> str:
    """
    Renders only a line, without executing control blocks. Safer than render()
    for some kind of use.
    """

    if not isinstance(context, Context):
        context = Context(context)

    line = Line([*parse_line(line)])

    return line.execute(context)
