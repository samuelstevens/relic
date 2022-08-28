import argparse

from .. import experiments
from .lib import logging, shared


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser(
        "delete", help="Delete experiments from your relic repository."
    )
    parser.add_argument(
        "--hashes",
        nargs="+",
        help="Experiment (prefix) hashes to delete.",
        default=[],
    )
    shared.add_filter_options(parser)

    parser.set_defaults(func=do_delete)


def do_delete(args: argparse.Namespace) -> int:
    # Delete all experiments specified by hash.
    for hash_prefix in args.hashes:
        to_delete = list(experiments.with_prefix(hash_prefix, args.project.root))
        if len(to_delete) == 0:
            logging.warn(f"There are no experiments with the prefix '{hash_prefix}'!")
            return 1
        elif len(to_delete) > 1:
            logging.warn(
                f"There are {len(to_delete)} experiments with the prefix '{hash_prefix}'. Not deleting any of them!"
            )
            return 1
        else:
            to_delete[0].delete()

    # Delete all experiments specified by --experiments
    if args.experiments:
        exp_fn, needs_trials = shared.make_experiment_fn(args.experiments)
        for exp in experiments.load_all(args.project, exp_fn, needs_trials):
            exp.delete()

    return 0
