import argparse
import pathlib
import sys

from . import cli, projects


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose",
        help="Whether to provide verbose output.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--root",
        help="Root relic directory",
        default=cli.DEFAULT_ROOT,
        type=str,
    )

    subparsers = parser.add_subparsers(help="Available commands.")

    add_init_parser(subparsers)
    cli.cat.add_parser(subparsers)
    cli.delete.add_parser(subparsers)
    cli.export.add_parser(subparsers)
    cli.ls.add_parser(subparsers)
    cli.merge.add_parser(subparsers)
    cli.modify.add_parser(subparsers)
    cli.plot.add_parser(subparsers)
    cli.versions.add_parser(subparsers)

    return parser


def add_init_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser("init", help="Initialize a relic repository.")
    parser.set_defaults(func=do_init)


def do_init(args: argparse.Namespace) -> None:
    root = pathlib.Path(args.root)
    try:
        projects.Project.new(root)
    except Exception as err:
        cli.lib.logging.error(str(err))


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    cli.lib.logging.init(args.verbose)

    if not hasattr(args, "func"):
        cli.lib.logging.error("No command specified.")
        parser.print_help()
        return 1

    if args.func == do_init:
        do_init(args)
        return 0

    # if we are doing anything besides initializing, get rid of root and don't let the subcommands use them.
    args.project = projects.Project(pathlib.Path(args.root))
    del args.root

    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
