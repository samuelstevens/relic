import argparse
import collections
import functools
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

import preface
from tabulate import tabulate

from .. import experiments, types
from . import lib

FormatFunc = Callable[[Any], str]
Handler = Callable[[experiments.Experiment], Tuple[str, Any]]
Row = List[Any]
Ordering = Callable[[Sequence[str], Sequence[Row]], List[Row]]
SpecialField = Literal["experiment", "trials"]


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser("ls", help="Show results from experiments.")

    parser = lib.shared.add_filter_options(parser)

    parser.add_argument(
        "--show",
        nargs="+",
        help="Columns to show. Keys can be regular expressions. Examples: --show epochs .*loss.*",
        default=[],
    )
    parser.add_argument(
        "--aggregator",
        help="Aggregate function to use on multiple trials.",
        default="mean",
        choices=list(lib.shared.AGGREGATOR_MAP.keys()),
    )
    parser.add_argument(
        "--sort",
        help="Fields (either config keys or metrics) to sort by. Provide multiple keys to break ties.",
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--hide",
        help="Fields (config keys) to not show.",
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--only",
        help="Fields (config keys) to only show. Overrides --show.",
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--all",
        help="Include experiments with 0 trials.",
        action="store_true",
    )
    parser.set_defaults(func=do_ls)


class Table:
    headers: List[str]
    rows: List[Row]

    def __init__(
        self,
        exps: Sequence[experiments.Experiment],
        special_handlers: Sequence[Handler],
        config_handlers: Sequence[Handler],
        metric_handlers: Sequence[Handler],
        orderings: Sequence[Ordering],
    ) -> None:

        columns: Dict[str, List[str]] = collections.defaultdict(list)

        # NOTE: embarassingly parallel.
        for experiment in exps:
            for handler in special_handlers:
                field, value = handler(experiment)
                columns[field].append(value)

            for handler in config_handlers:
                field, value = handler(experiment)
                columns[field].append(value)

            for handler in metric_handlers:
                field, value = handler(experiment)
                columns[field].append(value)

        self.headers = list(columns.keys())
        self.rows = [list(row) for row in zip(*columns.values())]

        # sort rows by the orderings
        for ordering in reversed(orderings):
            self.rows = ordering(self.headers, self.rows)

    def __str__(self) -> str:
        return tabulate(self.rows, headers=self.headers, floatfmt=".3g", missingval="-")


class ConfigHandler:
    def __init__(self, field: str):
        self.field = field

    def __call__(self, experiment: experiments.Experiment) -> Tuple[str, Any]:
        try:
            value = preface.dict.get(experiment.config, self.field)
        except KeyError:
            value = "-"

        return self.field, value

    def __str__(self) -> str:
        return f"<ConfigHandler(field={self.field})>"

    def __repr__(self) -> str:
        return str(self)


def _make_config_handlers(config_fields: Sequence[str]) -> List[Handler]:
    return [ConfigHandler(field) for field in config_fields]


class ShowHandler:
    def __init__(
        self,
        field_code: str,
        agg_fn: types.AggregatorFunc,
        filter_fn: types.FilterFn[experiments.Trial],
    ):
        self.field = lib.lang.compile(field_code)
        self.agg_fn = agg_fn
        self.filter_fn = filter_fn

    def __call__(self, experiment: experiments.Experiment) -> Tuple[str, Any]:

        value: Union[None, float, str, bool] = None

        values = []
        for trial in experiment:
            if not self.filter_fn(trial):
                continue

            values.append(self.field(trial))

        if values:
            if lib.lang.ast.isnumberlist(values):
                value = self.agg_fn(values)
            elif all(a == b for a, b in zip(values, values[1:])):
                value = f"{values[0]} (all)"
            else:
                value = ",".join(map(str, values))
        else:
            result = self.field(experiment)
            assert lib.lang.ast.isresult(result)
            value = result

        return str(self.field), value


def _make_show_handlers(
    fields: Sequence[str], aggregator: str, filter_fn: types.FilterFn[experiments.Trial]
) -> List[Handler]:
    """
    For each metric (epochs, training_loss, etc.), you must specify how to combine them over multiple trials.

    The default strategy is to use mean.
    """
    agg_fn = lib.shared.AGGREGATOR_MAP[aggregator]

    return [ShowHandler(field, agg_fn, filter_fn) for field in fields]


def _make_special_handlers(
    fields: Sequence[SpecialField], filter_fn: types.FilterFn[experiments.Trial]
) -> List[Handler]:
    handlers = []

    for field in fields:
        if field == "experiment":
            # TODO: eventually this should be the shortest length required to uniquely distinguish an experiment among all experiments in the relics directory.
            handlers.append(lambda exp: ("experiment", exp.hash[: len("experiment")]))
        elif field == "trials":
            handlers.append(
                lambda exp: (
                    "trials",
                    len([trial for trial in exp if filter_fn(trial)]),
                )
            )
        else:
            preface.never(field)

    return handlers


class OrderingObj:
    def __init__(self, field: str):
        self.field = field

    def __call__(self, headers: Sequence[str], rows: Sequence[Row]) -> List[Row]:
        try:
            i = headers.index(self.field)
        except ValueError:
            lib.logging.warn(
                f"Sorting by {self.field} but {self.field} is not in fields displayed!"
            )
            return rows  # type: ignore

        # puts None values at the end
        return sorted(rows, key=lambda x: (x[i] is None, x[i]))


def _parse_orderings(fields: Sequence[str]) -> List[Ordering]:
    return [OrderingObj(field) for field in fields]


def _filter_fields_in_table(
    fields: Sequence[str],
    differing: Set[str],
    hide: Set[str],
    only: Set[str],
    show: Set[str],
) -> List[str]:
    good_fields = []

    for field in fields:
        if field in hide:
            continue

        if only:
            if field in only:
                good_fields.append(field)

            continue

        if field in differing:
            good_fields.append(field)
        elif field in show:
            good_fields.append(field)
        elif field == "experiment":
            good_fields.append(field)
        elif field == "trials":
            good_fields.append(field)

    return good_fields


def make_table(
    exps: List[experiments.Experiment],
    aggregator: str,
    sorts: Optional[List[str]] = None,
    show: Optional[List[str]] = None,
    hide: Optional[List[str]] = None,
    only: Optional[List[str]] = None,
    trial_filters: Optional[List[str]] = None,
) -> Table:
    differing = set(experiments.differing_config_fields(exps))

    if sorts is None:
        sorts = []

    if show is None:
        show = []

    if hide is None:
        hide = []

    if only is None:
        only = []

    if trial_filters is None:
        trial_filters = []

    filter_fields = functools.partial(
        _filter_fields_in_table, differing=differing, hide=hide, only=only, show=show
    )

    special_fields: List[SpecialField] = filter_fields(["experiment", "trials"])  # type: ignore

    config_fields = filter_fields(
        sorted(
            set(
                preface.flattened(
                    [list(preface.dict.flattened(e.config).keys()) for e in exps]
                )
            )
        )
    )

    show_fields = [
        field
        for field in filter_fields(show)
        if field not in config_fields + special_fields  # type: ignore
    ]

    config_handlers = _make_config_handlers(config_fields)

    trial_filter_fn = lib.shared.make_trial_fn(trial_filters)

    show_handlers = _make_show_handlers(show_fields, aggregator, trial_filter_fn)

    orderings = _parse_orderings(sorts)

    special_handlers = _make_special_handlers(special_fields, trial_filter_fn)

    return Table(exps, special_handlers, config_handlers, show_handlers, orderings)


def make_table_from_args(args: argparse.Namespace) -> Optional[Table]:
    filter_fn = lib.shared.make_experiment_fn(args.experiments)

    exps = list(experiments.load_all(args.project, filter_fn))

    if not args.all:
        # Remove experiments with 0 trials
        exps = [e for e in exps if len(e) > 0]

    if not exps:
        lib.logging.info(f"No experiments that match {args.experiments}")
        return None

    return make_table(
        exps,
        args.aggregator,
        sorts=args.sort,
        show=args.show,
        hide=args.hide,
        only=args.only,
        trial_filters=args.trials,
    )


def do_ls(args: argparse.Namespace) -> int:
    table = make_table_from_args(args)

    print(table)

    return 1 if table is None else 0
