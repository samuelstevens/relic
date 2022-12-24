"""
This module provides some basic ways to save experiments efficiently, using torch when possible and JSON when not.

Right now it only uses torch in the interest of time. In the future, if torch is not available, relic should default to using JSON.
"""

import pickle
from typing import Any

import torch

from . import types


def move(obj: types.T, device: torch.device) -> types.T:
    if isinstance(obj, list):
        return [move(t, device) for t in obj]  # type: ignore

    if isinstance(obj, tuple):
        return tuple(move(t, device) for t in obj)  # type: ignore

    if isinstance(obj, dict):
        return {move(key, device): move(value, device) for key, value in obj.items()}  # type: ignore

    if hasattr(obj, "to"):
        return obj.to(device)  # type: ignore

    return obj


def dump(file: types.Path, obj: object) -> None:
    torch.save(
        move(obj, torch.device("cpu")), file, pickle_protocol=pickle.HIGHEST_PROTOCOL
    )


def load(file: types.Path) -> Any:
    return torch.load(file, map_location=torch.device("cpu"))  # type: ignore
