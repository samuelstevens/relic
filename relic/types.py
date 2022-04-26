import pathlib
import sys
from typing import Any, Callable, Dict, Iterable, TypeVar, Union

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

Config = Dict[str, Any]

Primitive = Union[str, int, float, bool, None]

Path = Union[str, pathlib.Path]

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

AggregatorFunc = Callable[[Iterable[float]], float]

FilterFn = Callable[[T], bool]


class Sortable(Protocol):
    def __lt__(self, __other: Any) -> bool:
        ...
