"""
Relic projects keep track of changes to your code that would affect one or more experiments.

A project can have multiple versions, each of which have their own run for each experiment. When you define a new version, all of your old experiments are invalidated.

A project is stored on disk in the relics/project.json file.
"""
import logging
import os
import pathlib
import shutil
from typing import Iterator, Set

from . import json

logger = logging.getLogger(__name__)


def model_dir(root: pathlib.Path) -> pathlib.Path:
    return root / "models"


def project_file(root: pathlib.Path) -> pathlib.Path:
    return root / "project.json"


class Project:
    _root: pathlib.Path
    _current: int = 1
    _versions: int = 1

    def __init__(self, root: pathlib.Path):
        self._root = root

        obj = json.load(project_file(root))
        self._current = obj["current"]

        for file in os.listdir(root):
            if file[0] != "v":
                continue
            num = int(file[1:])
            self._versions = max(self._versions, num)

        logger.debug(
            "Initialized project. [current: %s, total versions: %s]",
            self._current,
            self._versions,
        )

    def add_version(self, to_keep: Set[str]) -> None:
        self._versions += 1

        new_dir = self._root / f"v{self._versions}"

        new_dir.mkdir(exist_ok=True)
        (new_dir / ".keep").touch()

        if not to_keep:
            return

        for file in self.experiment_files():
            for hash in to_keep:
                if file.stem.startswith(hash):
                    logger.debug(
                        "Keeping %s from v%s in v%s",
                        file,
                        self._current,
                        self._versions,
                    )
                    shutil.copy2(file, new_dir / file.name)

    def use_version(self, version: int) -> None:
        if version > self._versions:
            raise ValueError(
                f"Can't set version to {version} because we only have {self._versions} versions!"
            )

        self._current = version
        self.save()

    def save(self) -> None:
        json.dump(project_file(self._root), {"current": self._current})

    @property
    def root(self) -> pathlib.Path:
        return self._root / f"v{self._current}"

    @classmethod
    def new(cls, root: pathlib.Path) -> "Project":
        model_dir(root).mkdir(parents=True, exist_ok=True)

        if project_file(root).exists():
            raise ValueError("Not creating new project file; file already exists!")

        json.dump(project_file(root), {"current": 1})
        (root / "v1").mkdir(exist_ok=True)

        return cls(root)

    def experiment_files(self) -> Iterator[pathlib.Path]:
        for file in os.listdir(self.root):
            path = self.root / file

            if not os.path.isfile(path):
                continue

            if path.suffix != ".relic":
                continue

            yield path

    @property
    def description(self) -> str:
        # TODO: if versions_str is really long, I should condense it somehow.
        versions_str = ", ".join("v" + str(i + 1) for i in range(self._versions))
        experiment_count = len(list(self.experiment_files()))

        lines = [
            f"* root: {self._root}/",
            f"* versions: {versions_str}",
            f"* current: v{self._current} ({experiment_count} experiments)",
        ]

        return "\n".join(lines)

    def __str__(self) -> str:
        return f"{self.root}"
