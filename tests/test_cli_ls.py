import argparse
import pathlib
import tempfile

from relic import cli, experiments, projects


def test_smoke() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        cli.ls.do_ls(args)


def test_show_experiment() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment = experiments.Experiment.new({}, args.project.root)
        experiment.add_trial({})

        expected = 0
        actual = cli.ls.do_ls(args)
        assert actual == expected


def test_make_table_empty() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        actual = cli.ls.make_table_from_args(args)

        assert actual is None


def test_table_with_one_row() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment = experiments.Experiment.new({}, args.project.root)
        experiment.add_trial({})

        actual = cli.ls.make_table_from_args(args)
        assert isinstance(actual, cli.ls.Table)

        assert actual is not None
        assert len(actual.rows) == 1
        assert actual.headers == ["experiment", "trials"]


def test_table_with_differing_fields() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment", "trials", "file"]


def test_table_with_experiment_filter1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--experiments", "(all (== finished True))"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 1
        assert actual.headers == ["experiment", "trials"]


def test_table_with_experiment_filter2() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--experiments", "(all (== finished True))"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False, "epochs": 100})
        experiment_a.add_trial({"finished": True, "epochs": 200})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True, "epochs": 200})
        experiment_b.add_trial({"finished": True, "epochs": 200})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 1
        assert actual.headers == ["experiment", "trials"]


def test_table_with_experiment_filter3() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--experiments", "(any (<= epochs 200))"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False, "epochs": 100})
        experiment_a.add_trial({"finished": True, "epochs": 200})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True, "epochs": 200})
        experiment_b.add_trial({"finished": True, "epochs": 200})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment", "trials", "file"]


def test_table_with_experiment_filter4() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(
        ["ls", "--experiments", "(all (and (>= epochs 200) (== finished True)))"]
    )

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False, "epochs": 100})
        experiment_a.add_trial({"finished": True, "epochs": 200})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True, "epochs": 200})
        experiment_b.add_trial({"finished": True, "epochs": 200})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 1
        assert actual.headers == ["experiment", "trials"]


def test_table_with_experiment_filter5() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(
        ["ls", "--experiments", "(any (and (== succeeded False) (== finished True)))"]
    )

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": True, "succeeded": True})
        experiment_a.add_trial({"finished": True, "succeeded": False})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True, "succeeded": True})
        experiment_b.add_trial({"finished": True, "succeeded": True})

        experiment_c = experiments.Experiment.new({"file": "c.txt"}, args.project.root)
        experiment_c.add_trial({"finished": True, "succeeded": True})
        experiment_c.add_trial({"finished": True, "succeeded": False})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment", "trials", "file"]


def test_table_with_experiment_filter6() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(
        ["ls", "--experiments", "(or (all (< epochs 100)) (all (> epochs 1000)))"]
    )

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"epochs": 50})
        experiment_a.add_trial({"epochs": 50})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"epochs": 50})
        experiment_b.add_trial({"epochs": 10000})

        experiment_c = experiments.Experiment.new({"file": "c.txt"}, args.project.root)
        experiment_c.add_trial({"epochs": 10000})
        experiment_c.add_trial({"epochs": 10000})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment", "trials", "file"]


def test_table_with_experiment_filter7() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--experiments", "(not (== file 'a.txt'))"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"epochs": 50})
        experiment_a.add_trial({"epochs": 50})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"epochs": 50})
        experiment_b.add_trial({"epochs": 10000})

        experiment_c = experiments.Experiment.new({"file": "c.txt"}, args.project.root)
        experiment_c.add_trial({"epochs": 10000})
        experiment_c.add_trial({"epochs": 10000})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment", "trials", "file"]


def test_table_with_trial_filter1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(
        ["ls", "--trials", "(and (== succeeded False) (== finished True)))"]
    )

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": True, "succeeded": True})
        experiment_a.add_trial({"finished": True, "succeeded": False})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True, "succeeded": False})
        experiment_b.add_trial({"finished": True, "succeeded": False})

        experiment_c = experiments.Experiment.new({"file": "c.txt"}, args.project.root)
        experiment_c.add_trial({"finished": True, "succeeded": True})
        experiment_c.add_trial({"finished": True, "succeeded": False})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 3
        assert actual.headers == ["experiment", "trials", "file"]


def test_table_with_only1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--only", "experiment"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment"]


def test_table_with_only2() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--only", "experiment", "file"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False})

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment", "file"]


def test_table_with_show1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--show", "finished", "name"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new(
            {"file": "a.txt", "name": "sam"}, args.project.root
        )
        experiment_a.add_trial({"finished": False})

        experiment_b = experiments.Experiment.new(
            {"file": "b.txt", "name": "sam"}, args.project.root
        )
        experiment_b.add_trial({"finished": True})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.headers == ["experiment", "trials", "file", "name", "finished"]


def test_table_with_order1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--sort", "file"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True})

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 2
        assert actual.rows[0][2] == "a.txt"
        assert actual.rows[1][2] == "b.txt"
        assert actual.headers == ["experiment", "trials", "file"]


def test_table_with_special_words1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(["ls", "--experiments", "(== trialcount 2)"])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False})

        actual = cli.ls.make_table_from_args(args)

        assert actual is not None
        assert len(actual.rows) == 1
        assert actual.headers == ["experiment", "trials"]


def test_table_with_special_words2() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(
        ["ls", "--experiments", "(like experimenthash |9527349cd0|)"]
    )

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        experiment_b = experiments.Experiment.new({"file": "b.txt"}, args.project.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        experiment_a = experiments.Experiment.new({"file": "a.txt"}, args.project.root)
        experiment_a.add_trial({"finished": False})

        actual = cli.ls.make_table_from_args(args)
        assert actual is not None
        assert len(actual.rows) == 1
        assert actual.headers == ["experiment", "trials"]


def test_table_regression1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.ls.add_parser(subparsers)
    args = parser.parse_args(
        [
            "ls",
            "--experiments",
            "(~ data.file |random-\\w+/4-chunks|)",
            "(like model.intrinsic_dimension |10000|)",
            "--trials",
            "(== finished True)",
            "--sort",
            "model.intrinsic_dimension",
            "data.file",
            "--show",
            "model.intrinsic_dimension",
        ]
    )

    def add(file: str, dim: int) -> None:
        experiment = experiments.Experiment.new(
            {
                "data": {"file": file},
                "model": {"intrinsic_dimension": dim},
            },
            args.project.root,
        )
        experiment.add_trial({"finished": True})
        experiment.add_trial({"finished": True})
        experiment.add_trial({"finished": True})

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        args.project = projects.Project.new(root)

        for i in range(10):
            add(f"data/random-letters/4-chunks/{i}.txt", 100000)

        actual = cli.ls.make_table_from_args(args)
        assert actual is not None
        assert len(actual.rows) == 10

        assert actual.rows[0][1] == 3
        assert actual.rows[0][2] == "data/random-letters/4-chunks/0.txt"
        assert actual.rows[0][3] == 100000

        assert actual.headers == [
            "experiment",
            "trials",
            "data.file",
            "model.intrinsic_dimension",
        ]
