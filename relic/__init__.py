"""
Package for managing versions of an experiment
"""

__version__ = "0.2.0"

import pathlib
from typing import Iterator, Optional

from . import cli, experiments, projects, types
from .experiments import Experiment, Trial


def new_experiment(
    config: types.Config, root: Optional[pathlib.Path] = None
) -> Experiment:
    if root is None:
        root = cli.DEFAULT_ROOT

    project = projects.Project(root)

    return Experiment.new(config, project.root)


def load_experiments(
    root: Optional[pathlib.Path] = None,
    filter_fn: types.FilterFn[Experiment] = lambda _: True,
) -> Iterator[Experiment]:
    if root is None:
        root = cli.DEFAULT_ROOT

    project = projects.Project(root)

    return experiments.load_all(project, filter_fn)


__all__ = ["new_experiment", "load_experiments", "Experiment", "Trial"]
