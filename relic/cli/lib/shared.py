"""
Shared parser options for various CLI options.
"""
import argparse
import statistics
from typing import Dict, Sequence

from ... import experiments, types
from . import lang

AGGREGATOR_MAP: Dict[str, types.AggregatorFunc] = {
    "mean": statistics.mean,
    "median": statistics.median,
    "mode": statistics.mode,
    "stdev": statistics.stdev,
    "sum": sum,
}


def add_filter_options(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "-e",
        "--experiments",
        nargs="+",
        help="Filter experiments based on results. Example: '(all (< epochs 1000))'",
        default=[],
    )
    parser.add_argument(
        "-t",
        "--trials",
        nargs="+",
        help="Filter trials based on results. Example: '(== succeeded True)'",
        default=[],
    )
    return parser


def make_experiment_fn(
    raw_filters: Sequence[str],
) -> types.FilterFn[experiments.Experiment]:
    filter_fns = [lang.experiment(raw_filter) for raw_filter in raw_filters]

    def filter_experiment(experiment: experiments.Experiment) -> bool:
        result = True
        for fn in filter_fns:
            result = result and fn(experiment)
        return result

    return filter_experiment


def make_trial_fn(
    raw_trial_filters: Sequence[str],
) -> types.FilterFn[experiments.Trial]:
    trial_fns = [lang.trial(raw_trial_filter) for raw_trial_filter in raw_trial_filters]

    def filter_trials(trial: experiments.Trial) -> bool:
        result = True
        for fn in trial_fns:
            result = result and fn(trial)
        return result

    return filter_trials
