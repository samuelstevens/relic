"""
This module provides some basic ways to save experiments efficiently, using torch when possible and JSON when not.

Right now it only uses torch in the interest of time. In the future, if torch is not available, relic should default to using JSON.
"""

import pickle
from typing import Any

import torch

from . import types


def dump(file: types.Path, obj: object) -> None:
    torch.save(obj, file, pickle_protocol=pickle.HIGHEST_PROTOCOL)


def load(file: types.Path) -> Any:
    return torch.load(file)  # type: ignore
