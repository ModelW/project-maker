import json
import re
from typing import Sequence

from unidecode import unidecode

IS_CAMEL_WORD = re.compile(r"[A-Z][a-z]*")
IS_NUM = re.compile(r"\d+")
IS_ABBREV = re.compile(r"[A-Z]{2,}")
IS_SNAKE_WORD = re.compile(r"[a-z]+")


def smart_split_name(s: str) -> Sequence[str]:
    """
    Smart name splitting. Understand both CamelCase and snake_case, including
    camel case abbreviations like `setIBAN`. Returns the lowercase parts of the
    name. Everything that isn't letters or numbers will be discarded.
    """

    out = []
    pos = 0
    s = unidecode(s)

    while pos < len(s):
        m_camel_word = IS_CAMEL_WORD.search(s, pos)
        m_num = IS_NUM.search(s, pos)
        m_abbrev = IS_ABBREV.search(s, pos)
        m_snake_word = IS_SNAKE_WORD.search(s, pos)

        match_pos = min(
            (x.start() for x in [m_camel_word, m_num, m_abbrev, m_snake_word] if x),
            default=-1,
        )

        if match_pos < 0:
            break

        if m_abbrev and m_abbrev.start() == match_pos:
            if m_abbrev.end() == len(s):
                out.append(m_abbrev.group(0))
                pos = m_abbrev.end()
            else:
                next_c = s[m_abbrev.end()]

                if next_c.islower():
                    out.append(m_abbrev.group(0)[0:-1])
                    pos = m_abbrev.end() - 1
                else:
                    out.append(m_abbrev.group(0))
                    pos = m_abbrev.end()
        elif m_num and m_num.start() == match_pos:
            out.append(m_num.group(0))
            pos = m_num.end()
        elif m_camel_word and m_camel_word.start() == match_pos:
            out.append(m_camel_word.group(0))
            pos = m_camel_word.end()
        elif m_snake_word and m_snake_word.start() == match_pos:
            out.append(m_snake_word.group(0))
            pos = m_snake_word.end()
        else:
            pos += 1

    return tuple(x.lower() for x in out)


def name_camel_up(s: Sequence[str]) -> str:
    """
    Generates CamelCase name, starting with an uppercase letter.

    >>> assert name_camel_up(['foo', 'bar']) == 'FooBar'
    """

    was_num = False
    out = ""

    for x in s:
        if was_num and x.isnumeric():
            out += "_"

        out += x.title()
        was_num = x.isnumeric()

    return out


def name_camel_low(s: Sequence[str]) -> str:
    """
    Generates CamelCase name, starting with a lowercase letter.

    >>> assert name_camel_low(['foo', 'bar']) == 'fooBar'
    """

    was_num = False
    out = "".join(s[:1])

    for x in s[1:]:
        if was_num and x.isnumeric():
            out += "_"

        out += x.title()
        was_num = x.isnumeric()

    return out


def name_snake(s: Sequence[str]) -> str:
    """
    Generates a snake_case name.

    >>> assert name_snake(['foo', 'bar']) == 'foo_bar'
    """

    return "_".join(s)


def name_dashed(s: Sequence[str]) -> str:
    """
    Generates a dash-case name.

    >>> assert name_snake(['foo', 'bar']) == 'foo-bar'
    """

    return "-".join(s)


def generate_declinations(name: str):
    bits = smart_split_name(name)

    return dict(
        natural=name,
        natural_double_quoted=json.dumps(name, ensure_ascii=False).strip('"'),
        snake=name_snake(bits),
        snake_up=name_snake(bits).upper(),
        camel_low=name_camel_low(bits),
        camel_up=name_camel_up(bits),
        dashed=name_dashed(bits),
    )
