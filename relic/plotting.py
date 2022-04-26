"""
Example usage:

relic.plot(
    experiments,
    plotting="epochs",
    with_respect_to="dropout",
    controlling_for=["intrinsic_dimension", "learning_rate"]
    aggregating_with=statistics.mean
)

TODO:
* If the with_respect_to is a string (anything that's not a number) then we should use a bar chart.
"""
import collections
import statistics
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple, Union

import matplotlib.pyplot as plt
import preface

from . import experiments, types

MaybeList = Union[None, types.T, List[types.T]]

# Lines are indexed by their unique combination of variables that are controlled for.
# Suppose we control for model.dropout and training.lr. Then all experiments that have
# the same value for dropout and learning rate have the same key.
Key = Tuple[Tuple[str, object], ...]


class Point(NamedTuple):
    aggregate: float
    min: float
    max: float


def _ensure_list(x: MaybeList[types.T]) -> List[types.T]:
    if x is None:
        return []
    if not isinstance(x, list):
        return [x]

    return x


def _prettify(key: Key) -> str:
    """
    Human readable key.
    """
    return ", ".join(f"{var}: {value}" for var, value in key)


def _metric_value(
    experiment: experiments.Experiment, metric: str, agg_fn: types.AggregatorFunc
) -> float:
    values = []
    for trial in experiment:
        if preface.dict.contains(trial, metric):
            values.append(preface.dict.get(trial, metric))
    try:
        return agg_fn(values)
    except statistics.StatisticsError as err:
        print(repr(experiment))
        raise err


def get_differences(
    exps: Sequence[experiments.Experiment],
) -> Dict[str, Set[types.Sortable]]:
    """
    Returns a dictionary of fields that have different values, and the values associated with each field.
    """
    fields = experiments.differing_config_fields(exps)

    return {
        field: {
            preface.dict.get(exp.config, field)
            for exp in exps
            if preface.dict.contains(exp.config, field)
        }
        for field in fields
    }


def make_experiment_series(
    exps: Sequence[experiments.Experiment], controlling_for: List[str]
) -> Dict[Key, List[experiments.Experiment]]:
    series = collections.defaultdict(list)

    # For each combination of variables in controlling_for, we will plot a new series.
    for exp in exps:
        # Ignore experiments with no trials.
        if len(exp) == 0:
            continue

        key = tuple(
            (variable, preface.dict.get(exp.config, variable))
            for variable in controlling_for
        )
        series[key].append(exp)

    return series


def plot(
    exps: Sequence[experiments.Experiment],
    plotting: str,
    with_respect_to: str,
    controlling_for: MaybeList[str] = None,
    aggregating_with: types.AggregatorFunc = statistics.mean,
    title: Optional[str] = None,
) -> None:

    controlling_for = _ensure_list(controlling_for)

    experiment_series = make_experiment_series(exps, controlling_for)

    differences = {
        key: get_differences(exps) for key, exps in experiment_series.items()
    }

    for key, diffs in differences.items():
        # Don't print the key we're using to compare
        diffs.pop(with_respect_to, None)
        if not diffs:
            continue

        print(f"Differences in the '{_prettify(key)}' series:")

        for field, values in diffs.items():
            print(
                f"* {field} has {len(values)} different values: {', '.join(sorted(map(str, values)))}"
            )
        print()

    series = {}

    for key, exps in experiment_series.items():
        complete_xy_mapping = collections.defaultdict(list)
        for exp in exps:
            complete_xy_mapping[preface.dict.get(exp.config, with_respect_to)].append(
                _metric_value(exp, plotting, aggregating_with)
            )
        aggregate_xy_mapping = {
            x: Point(aggregating_with(y), min(y), max(y))
            for x, y in complete_xy_mapping.items()
        }
        series[key] = aggregate_xy_mapping

    fig, ax = plt.subplots(1, 1)

    master_xs: List[types.Sortable] = []
    for xy_mapping in series.values():
        if len(xy_mapping) > len(master_xs):
            master_xs = sorted(xy_mapping)

    # plot a dummy on the axis
    ax.plot(master_xs, [0 for _ in master_xs], linewidth=0, marker=None)

    for key, xy_mapping in sorted(series.items()):
        xs = sorted(xy_mapping)
        ys = [xy_mapping[x].aggregate for x in xs]
        mins = [xy_mapping[x].min for x in xs]
        maxs = [xy_mapping[x].max for x in xs]

        line = ax.plot(xs, ys, label=_prettify(key), marker="o")[0]
        ax.fill_between(xs, maxs, mins, alpha=0.1, color=line._color)

    if title:
        fig.suptitle(title)
    else:
        fig.suptitle(f"{plotting}")
    fig.tight_layout()
    ax.set_xlabel(with_respect_to)
    ax.set_ylabel(plotting)
    ax.legend()

    plt.show(block=True)
