import argparse
import os
import pathlib
import sys
import typing
from typing import Callable, Dict, Optional

from .. import experiments, json, projects
from .lib import logging

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

"""
Trial conflict resolution.

Sometimes we will have two trials that are in conflict. Which trial should we pick?
"""

ConflictStrategy = Literal["longer", "src", "dst", "none", "both", "keep"]
ConflictFn = Callable[[experiments.Trial, experiments.Trial], bool]


class ConflictResolutionError(Exception):
    def __init__(
        self,
        src_trial: experiments.Trial,
        dst_trial: experiments.Trial,
    ):
        self.src_trial = src_trial
        self.dst_trial = dst_trial


def no_resolution(src_trial: experiments.Trial, dst_trial: experiments.Trial) -> bool:
    raise ConflictResolutionError(src_trial, dst_trial)


def use_longer_trial(
    src_trial: experiments.Trial, dst_trial: experiments.Trial
) -> bool:
    return len(json.dumpb(src_trial)) > len(json.dumpb(dst_trial))


def use_source_trial(
    src_trial: experiments.Trial, dst_trial: experiments.Trial
) -> bool:
    return True


def use_destination_trial(
    src_trial: experiments.Trial, dst_trial: experiments.Trial
) -> bool:
    return False


conflict_choices: Dict[ConflictStrategy, ConflictFn] = {
    "longer": use_longer_trial,
    "src": use_source_trial,
    "dst": use_destination_trial,
    "none": no_resolution,
    "keep": no_resolution,
}


# Argument parsing


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser_merge = subparsers.add_parser("merge", help="Merge two relic directories.")
    parser_merge.add_argument(
        "sources", help="One or more relics directories to merge from", nargs="+"
    )
    parser_merge.add_argument(
        "destination",
        help="Destination directory.",
    )
    parser_merge.add_argument(
        "--conflicts",
        help="How to resolve trial conflicts. 'longer' chooses the longer trial",
        choices=typing.get_args(ConflictStrategy),
        default="none",
    )
    parser_merge.set_defaults(func=do_merge)


def do_merge(args: argparse.Namespace) -> int:
    dst_project = projects.Project(pathlib.Path(args.destination))

    conflict_strategy: ConflictStrategy = args.conflicts

    for source in args.sources:
        merge_source_proj(
            projects.Project(pathlib.Path(source)),
            dst_project,
            conflict_strategy,
        )

    return 0


def add_experiment(src_exp: experiments.Experiment, dst_proj: projects.Project) -> None:
    logging.info(
        f"Adding experiment '{src_exp}' from source '{src_exp.root}' to destination '{dst_proj}' because experiment is not in destination."
    )

    dst_exp = experiments.Experiment.new(src_exp.config, dst_proj.root)

    for trial in src_exp:
        original_model_path = src_exp.model_path(trial["instance"])
        if not os.path.exists(original_model_path):
            original_model_path = None  # type: ignore
        dst_exp.add_trial(trial, model_path=original_model_path)


def add_extra_trials(
    src_exp: experiments.Experiment, dst_exp: experiments.Experiment
) -> None:
    logging.debug(
        "Source experiment %s (%d trials) has more trials than destination experiment (%d trials). Moving all extra (%d) trials to destination.",
        src_exp,
        len(src_exp),
        len(dst_exp),
        len(src_exp) - len(dst_exp),
    )

    original_model_path: Optional[pathlib.Path]

    for i, trial in list(enumerate(src_exp))[len(dst_exp) :]:
        logging.info(f"Adding trial {i} to destination experiment {dst_exp}")
        original_model_path = src_exp.model_path(trial["instance"])
        if not os.path.exists(original_model_path):
            original_model_path = None
        dst_exp.add_trial(trial, model_path=original_model_path)


def merge_source_exp(
    src_exp: experiments.Experiment,
    dst_proj: projects.Project,
    conflict_strategy: ConflictStrategy,
) -> None:
    # experiment already exists in dst_proj
    dst_exp = experiments.Experiment.load(dst_proj.root, src_exp.hash)

    if dst_exp.config != src_exp.config:
        msg = f"Source experiment {src_exp} has the same hash as destination experiment {dst_exp} but has a different config! Something is very broken!"
        logging.error(msg)
        raise RuntimeError(msg)

    logging.debug(
        "Merging trials from source experiment %s into destination %s.",
        src_exp,
        dst_proj,
    )
    original_model_path: Optional[pathlib.Path]

    if conflict_strategy == "keep":
        # Keep all trials
        for i, src_trial in enumerate(src_exp):
            original_model_path = src_exp.model_path(i)
            if not os.path.exists(original_model_path):
                original_model_path = None
            del src_trial["instance"]
            dst_exp.add_trial(src_trial, original_model_path)

    else:
        assert conflict_strategy in conflict_choices
        conflict_fn = conflict_choices[conflict_strategy]
        for i, (src_trial, dst_trial) in enumerate(zip(src_exp, dst_exp)):
            if src_trial == dst_trial:
                continue

            try:
                if conflict_fn(src_trial, dst_trial):
                    logging.info(
                        f"Replacing trial {i} in experiment {dst_exp} from experiment {src_exp}."
                    )
                    original_model_path = src_exp.model_path(i)
                    if not os.path.exists(original_model_path):
                        original_model_path = None
                    dst_exp.update_trial(src_trial, original_model_path)
                else:
                    logging.info(
                        f"Keeping trial {i} in destination experiment {dst_exp}; ignoring trial {i} in source experiment {src_exp}."
                    )
            except ConflictResolutionError:
                msg = f"Trial {i} is different between source experiment {src_exp} in {src_exp.root} and destination experiment {dst_exp}! This is very bad!"
                logging.error(msg)
                raise RuntimeError(msg)

        if len(src_exp) > len(dst_exp):
            add_extra_trials(src_exp, dst_exp)


def merge_source_proj(
    src_proj: projects.Project,
    dst_proj: projects.Project,
    conflict_strategy: ConflictStrategy,
) -> None:
    for src_exp in experiments.load_all(src_proj):
        if not experiments.Experiment.exists(dst_proj.root, src_exp.hash):
            add_experiment(src_exp, dst_proj)
        else:
            merge_source_exp(src_exp, dst_proj, conflict_strategy)
