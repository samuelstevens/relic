import argparse
import datetime
import os
import pathlib

from .. import experiments, types
from .lib import logging

FORMATS = ["csv", "json"]


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser(
        "export", help="Export your repository into file formats."
    )
    parser.add_argument(
        "--format", help="File format to export to.", choices=FORMATS, default="json"
    )
    parser.add_argument(
        "--dir",
        help="Directory to write exported files to.",
        default=f"exports_{datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}",
    )
    parser.set_defaults(func=do_export)


def _filepath(root: types.Path, experiment: experiments.Experiment) -> pathlib.Path:
    return pathlib.Path(root) / experiment.hash


def do_export(args: argparse.Namespace) -> None:
    try:
        os.makedirs(args.dir)
    except OSError:
        if os.listdir(args.dir):
            logging.error(
                "Not writing to %s because there are existing files in it!", args.dir
            )
            return

    if args.format == "json":
        raise NotImplementedError()
    elif args.format == "csv":
        raise NotImplementedError()
    else:
        raise ValueError(f"Format '{args.format}' is not supported!")
