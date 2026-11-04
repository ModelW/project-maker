"""Iteration helpers used by the health app."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def n_uple[T](seq: Iterable[T], n: int = 2) -> Iterator[tuple[T, ...]]:
    """
    Iterates over the provided iterator and returns n-uples of size n.
    """

    out = []

    for item in seq:
        out.append(item)

        if len(out) == n:
            yield tuple(out)
            out.pop(0)
