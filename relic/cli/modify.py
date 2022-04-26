import argparse
import copy
from typing import Callable, Dict, Iterator

import preface

from .. import experiments, types
from .lib import logging, shared


def _to_bool(val: str) -> bool:
    if val.lower() in ("true", "t"):
        return True

    if val.lower() in ("false", "f"):
        return False

    raise ValueError(f"Value '{val}' is not a valid boolean! Use T or F!")


TYPE_LIST = [int, float, str, bool]
TYPE_MAP: Dict[str, Callable[[str], object]] = {
    "int": int,
    "float": float,
    "str": str,
    "bool": _to_bool,
}


class ConflictStrategy(preface.SumType):
    more_trials = preface.SumType.auto()
    interactive = preface.SumType.auto()
    no_resolution = preface.SumType.auto()
    after = preface.SumType.auto()
    before = preface.SumType.auto()
    has_model = preface.SumType.auto()


def _add_field_option(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "field",
        help="Configuration field. Use a '.'-separated field, like 'model.n_positions'.",
    )
    return parser


def _add_conflicts_option(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--conflicts",
        help="How to handle conflicts",
        choices=list(map(str, ConflictStrategy)),
        default=str(ConflictStrategy.no_resolution),
    )
    return parser


def _add_add_parser(
    subparser: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    """
    Add a subparser for the 'modify add' name. Sorry for the awful function name!
    """
    parser = subparser.add_parser("add", help="Add a new default configuration option.")
    parser = shared.add_filter_options(parser)
    parser = _add_field_option(parser)
    parser = _add_conflicts_option(parser)

    parser.add_argument(
        "type",
        help="data type.",
        choices=TYPE_MAP.keys(),
    )
    parser.add_argument(
        "value",
        help="default value to use with existing configurations (if it does not exist already)",
    )
    parser.set_defaults(func=do_add)


def _add_rename_parser(
    subparser: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparser.add_parser("rename", help="Rename a configuration option.")
    parser = shared.add_filter_options(parser)
    parser = _add_conflicts_option(parser)

    parser.add_argument(
        "old_field",
        help="Old configuration field name. Use a '.'-separated field, like 'model.n_positions'.",
    )
    parser.add_argument(
        "new_field",
        help="New configuration field name. Use a '.'-separated field, like 'model.n_positions'.",
    )
    parser.set_defaults(func=do_rename)


def _add_remove_parser(
    subparser: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparser.add_parser("remove", help="Add a new configuation option")
    parser = shared.add_filter_options(parser)
    parser = _add_field_option(parser)
    parser = _add_conflicts_option(parser)
    parser.set_defaults(func=do_remove)


def _add_change_parser(
    subparser: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparser.add_parser("change", help="Change a configuation value")
    parser = shared.add_filter_options(parser)
    parser = _add_field_option(parser)
    parser = _add_conflicts_option(parser)

    parser.add_argument(
        "type",
        help="data type.",
        choices=TYPE_MAP.keys(),
    )
    parser.add_argument(
        "value",
        help="default value to use with existing configurations (if it does not exist already)",
    )
    parser.set_defaults(func=do_change)


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser(
        "modify", help="Modify existing experiment config options"
    )
    parser.add_argument(
        "--act",
        help="actually make the change. Otherwise, just show the modification that would be made.",
        action="store_true",
    )

    modify_subparsers = parser.add_subparsers(help="Available commands.")

    _add_add_parser(modify_subparsers)
    _add_remove_parser(modify_subparsers)
    _add_rename_parser(modify_subparsers)
    _add_change_parser(modify_subparsers)

    # SICK hack. Ignore the args argument. So that we return a valid int value, we return None or True => True => 1 => Failure!
    parser.set_defaults(func=lambda: print_help(parser))


def print_help(parser: argparse.ArgumentParser) -> int:
    parser.print_help()
    return 1


def load_experiments(args: argparse.Namespace) -> Iterator[experiments.Experiment]:
    filter_fn = shared.make_experiment_fn(args.experiments)
    return experiments.load_all(args.project, filter_fn)


def _update_experiment(
    old_exp: experiments.Experiment,
    new_config: types.Config,
    conflict_strategy: ConflictStrategy,
) -> None:
    # 1. create new experiment with new config
    new_exp = experiments.Experiment.new(new_config, old_exp.root)

    if len(old_exp) == 0:  # No existing trials.
        old_exp.delete()
        return

    if len(new_exp) == 0:
        # New experiment has no existing trials. Copying is easy
        copy_trials(old_exp, new_exp)
        old_exp.delete()
        return

    assert len(new_exp) > 0 and len(old_exp) > 0
    logging.warn(
        "New experiment already exists and has existing trials. Attempting to resolve the conflict. [old trials: %s, new trials: %s]",
        len(old_exp),
        len(new_exp),
    )

    # The new_exp already exists. What should we do with conflicts?

    # Sometimes we just want to use the one with the most trials.
    if conflict_strategy is ConflictStrategy.more_trials:
        if len(old_exp) == len(new_exp):
            logging.warn(
                "Equal number of trials. I don't know what to do! [trials: %s]",
                len(old_exp),
            )
            raise RuntimeError()

        if len(old_exp) > len(new_exp):
            # Use old trials
            new_exp.delete_trials()
            copy_trials(old_exp, new_exp)

        old_exp.delete()

    # Othertimes we'd like to do it interactively.
    elif conflict_strategy is ConflictStrategy.interactive:

        def status_str(exp: experiments.Experiment) -> str:
            hash = exp.hash
            trials = len(exp)
            saved = sum(1 for t, _ in enumerate(exp) if exp.model_exists(t))
            return f"Hash: {hash}\nTrials: {trials}\nSaved models: {saved}"

        # Show some information about the different trials.
        print("---")
        print(f"After modifying:\n{status_str(old_exp)}")
        print("---")
        print(f"After modifying:\n{status_str(new_exp)}")

        # Ask the user to choose a trial.
        print(
            "Do you want to use the trials from before modification, or from after modification?"
        )
        user_decision = ""
        while user_decision not in ("a", "b"):
            user_decision = input("(b)efore, (a)fter: ").strip()[0].lower()

        if user_decision == "a":
            print("Using trials from after modification.")
        elif user_decision == "b":
            new_exp.delete_trials()
            copy_trials(old_exp, new_exp)
            print("Using trials from before modification.")
        else:
            raise RuntimeError()

        old_exp.delete()

    elif conflict_strategy is ConflictStrategy.no_resolution:
        raise RuntimeError()

    elif conflict_strategy is ConflictStrategy.has_model:
        raise NotImplementedError()

    elif conflict_strategy is ConflictStrategy.before:
        new_exp.delete_trials()
        copy_trials(old_exp, new_exp)
        print("Using trials from before modification.")
        old_exp.delete()
    elif conflict_strategy is ConflictStrategy.after:
        print("Using trials from after modification.")
        old_exp.delete()

    # There might be other options in the future.
    else:
        preface.never(conflict_strategy)


def copy_trials(
    old_exp: experiments.Experiment, new_exp: experiments.Experiment
) -> None:
    for i, trial in enumerate(old_exp):
        assert trial["instance"] == i

        model_path = None
        if old_exp.model_exists(i):
            model_path = old_exp.model_path(i)

        new_exp.add_trial(trial, model_path)


def do_add(args: argparse.Namespace) -> int:
    default_value = TYPE_MAP[args.type](args.value)

    for old_experiment in load_experiments(args):
        new_config = copy.deepcopy(old_experiment.config)
        if preface.dict.contains(new_config, args.field):
            logging.debug(
                f"Not setting field '{args.field}' in experiment '{old_experiment}' because it already has value {preface.dict.get(new_config, args.field)}."
            )
            continue

        preface.dict.set(new_config, args.field, default_value)

        if args.act:
            _update_experiment(
                old_experiment, new_config, ConflictStrategy.new(args.conflicts)
            )
        else:
            logging.info(
                f"1. Add '{args.field}: {default_value}' to experiment {old_experiment}'s config. \n2. Re-hash the experiment and write to disk.\n3. Delete the old experiment."
            )

    return 0


def do_rename(args: argparse.Namespace) -> int:
    for old_experiment in load_experiments(args):
        # Remove and add the field from configurations.
        new_config = copy.deepcopy(old_experiment.config)
        if not preface.dict.contains(new_config, args.old_field):
            logging.debug(
                f"Not renaming missing field '{args.old_field}' in experiment '{old_experiment}'."
            )
            continue

        value = preface.dict.get(new_config, args.old_field)
        preface.dict.delete(new_config, args.old_field)
        preface.dict.set(new_config, args.new_field, value)

        if args.act:
            _update_experiment(
                old_experiment, new_config, ConflictStrategy.new(args.conflicts)
            )
        else:
            logging.info(
                f"1. Rename '{args.old_field}' from experiment {old_experiment}'s config to '{args.new_field}'. \n2. Re-hash the experiment and write to disk.\n3. Delete the old experiment."
            )

    return 0


def do_remove(args: argparse.Namespace) -> int:
    for old_experiment in load_experiments(args):
        # Remove the field from configurations.
        new_config = copy.deepcopy(old_experiment.config)
        if not preface.dict.contains(new_config, args.field):
            logging.debug(
                f"Not removing missing field '{args.field}' from experiment '{old_experiment}'."
            )
            continue

        preface.dict.delete(new_config, args.field)

        if args.act:
            _update_experiment(
                old_experiment, new_config, ConflictStrategy.new(args.conflicts)
            )
        else:
            logging.info(
                f"1. Remove '{args.field}' from experiment {old_experiment}'s config. \n2. Re-hash the experiment and write to disk.\n3. Delete the old experiment."
            )

    return 0


def do_change(args: argparse.Namespace) -> int:
    new_value = TYPE_MAP[args.type](args.value)

    for old_experiment in load_experiments(args):
        new_config = copy.deepcopy(old_experiment.config)
        if not preface.dict.contains(new_config, args.field):
            logging.debug(
                f"Not updating field '{args.field}' in experiment '{old_experiment}' because it does not yet have a value."
            )
            continue

        preface.dict.set(new_config, args.field, new_value)

        if args.act:
            _update_experiment(
                old_experiment, new_config, ConflictStrategy.new(args.conflicts)
            )
        else:
            logging.info(
                f"1. Set '{args.field}: {new_value}' in experiment {old_experiment}'s config. \n2. Re-hash the experiment and write to disk.\n3. Delete the old experiment."
            )

    return 0
