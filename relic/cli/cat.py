import argparse
import json

from .. import experiments
from . import lib


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser("cat", help="Show single experiment.")

    parser = lib.shared.add_filter_options(parser)

    parser.set_defaults(func=do_cat)


def do_cat(args: argparse.Namespace) -> int:
    filter_fn, needs_trials = lib.shared.make_experiment_fn(args.experiments)

    exps = list(experiments.load_all(args.project, filter_fn, needs_trials))

    if len(exps) > 1:
        lib.logging.warn(
            "Showing more than one experiment. [experiments: %s]", len(exps)
        )

    for exp in exps:
        print(json.dumps(exp.config))

    return 0
