import argparse


def add_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    parser = subparsers.add_parser("versions", help="Manage your project versions")
    parser.add_argument(
        "--new",
        help="Move to a new version (as a result of a bug fix)",
        action="store_true",
    )
    parser.add_argument(
        "--use",
        help="Use a particular version of your project",
        type=int,
    )
    parser.set_defaults(func=do_version)


def do_version(args: argparse.Namespace) -> int:
    if args.new:
        args.project.add_version()
    elif args.use:
        assert isinstance(args.use, int)
        args.project.use_version(args.use)

    # just describe versions
    print(args.project.description)

    return 0
