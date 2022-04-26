import argparse

from .. import experiments
from .lib import shared


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser("plot", help="Plot results.")

    parser = shared.add_filter_options(parser)

    parser.add_argument(
        "-y", "--y-axis", help="Metric to plot on the y-axis.", required=True
    )
    parser.add_argument(
        "-x", "--x-axis", help="Metric to plot on the x-axis.", required=True
    )
    parser.add_argument(
        "--control-for",
        nargs="+",
        default=[],
        help="Metrics that should be kept separate.",
    )
    parser.add_argument(
        "--trial-aggregator",
        help="Aggregate function to use on multiple trials.",
        default="mean",
        choices=list(shared.AGGREGATOR_MAP.keys()),
    )
    parser.add_argument(
        "--experiment-aggregator",
        help="Aggregate function to use on multiple experiments.",
        default="mean",
        choices=list(shared.AGGREGATOR_MAP.keys()),
    )
    parser.add_argument("--title", help="Plot title.", default=None)
    parser.set_defaults(func=do_plot)


def do_plot(args: argparse.Namespace) -> int:
    filter_fn = shared.make_experiment_fn(args.experiments)

    exps = list(experiments.load_all(args.project, filter_fn))

    # filter experiments with 0 trials
    exps = [e for e in exps if len(e) > 0]

    # Only import plotting if we need it.
    from .. import plotting

    plotting.plot(
        exps,
        args.y_axis,
        with_respect_to=args.x_axis,
        controlling_for=args.control_for,
        aggregating_with=shared.AGGREGATOR_MAP[args.experiment_aggregator],
        title=args.title,
    )

    return 1
