from typing import Any

import orjson

# needs 'as ...' so mypy doesn't complain
from orjson import JSONDecodeError as JSONDecodeError  # noqa: F401

from . import types


def load(file: types.Path) -> Any:
    with open(file, "rb") as fp:
        return loadb(fp.read())


def loadb(b: bytes) -> Any:
    return orjson.loads(b)


def dumpb(obj: Any, indent: bool = False) -> bytes:
    option = orjson.OPT_SORT_KEYS
    if indent:
        option |= orjson.OPT_INDENT_2

    return orjson.dumps(obj, option=option)


def dump(file: types.Path, obj: Any, indent: bool = False) -> None:
    with open(file, "wb") as fp:
        fp.write(dumpb(obj, indent=indent))
