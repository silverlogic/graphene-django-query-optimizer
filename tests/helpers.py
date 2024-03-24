import re

from query_optimizer.typing import NamedTuple, TypedDict, TypeVar, Union

__all__ = [
    "parametrize_helper",
]


TNamedTuple = TypeVar("TNamedTuple", bound=NamedTuple)


class ParametrizeArgs(TypedDict):
    argnames: list[str]
    argvalues: list[TNamedTuple]
    ids: list[str]


def parametrize_helper(__tests: dict[str, TNamedTuple], /) -> ParametrizeArgs:
    """Construct parametrize input while setting test IDs."""
    assert __tests, "I need some tests, please!"  # noqa: S101
    values = list(__tests.values())
    try:
        return ParametrizeArgs(
            argnames=list(values[0].__class__.__annotations__),
            argvalues=values,
            ids=list(__tests),
        )
    except AttributeError as error:
        msg = "Improper configuration. Did you use a NamedTuple for TNamedTuple?"
        raise RuntimeError(msg) from error


class like:
    """Compares a string to a regular expression pattern."""

    def __init__(self, query: str) -> None:
        self.pattern: re.Pattern[str] = re.compile(query)

    def __eq__(self, other: str) -> bool:
        if not isinstance(other, str):
            return False
        return self.pattern.match(other) is not None


class has:
    """Does the compared string contain the specified regular expression patterns?"""

    def __init__(self, *patterns: Union[str, like]) -> None:
        self.patterns = patterns

    def __eq__(self, other: str) -> bool:
        if not isinstance(other, str):
            return False
        return all(pattern in other for pattern in self.patterns)
