import argparse
import pathlib
import tempfile

import pytest

from relic import cli, experiments, projects


def test_merge1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(["merge", str(root_b), str(root_a)])

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project_a.root)
        experiment_a.add_trial({"finished": True})

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        cli.merge.do_merge(args)

        project_a_experiments = list(experiments.load_all(project_a))

        assert len(project_a_experiments) == 1
        assert len(project_a_experiments[0]) == 2

        for trial in project_a_experiments[0]:
            assert trial["finished"] is True


def test_merge2() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(["merge", str(root_b), str(root_a)])

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        cli.merge.do_merge(args)

        project_a_experiments = list(experiments.load_all(project_a))

        assert len(project_a_experiments) == 1
        assert len(project_a_experiments[0]) == 2

        for trial in project_a_experiments[0]:
            assert trial["finished"] is True


def test_merge_error2() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(["merge", str(root_b), str(root_a)])

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project_a.root)
        experiment_a.add_trial({"finished": True})
        experiment_a.add_trial({})

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        with pytest.raises(RuntimeError):
            cli.merge.do_merge(args)


def test_merge_longer1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Available commands.")
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(
            ["merge", str(root_b), str(root_a), "--conflicts", "longer"]
        )

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project_a.root)
        experiment_a.add_trial({"finished": True})
        experiment_a.add_trial({})

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        cli.merge.do_merge(args)

        project_a_experiments = list(experiments.load_all(project_a))

        assert len(project_a_experiments) == 1
        assert len(project_a_experiments[0]) == 2

        for trial in project_a_experiments[0]:
            assert trial["finished"] is True


def test_merge_longer2() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(
            ["merge", str(root_b), str(root_a), "--conflicts", "longer"]
        )

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project_a.root)
        experiment_a.add_trial({"finished": True})
        experiment_a.add_trial({"finished": True})
        experiment_a.add_trial({})

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        cli.merge.do_merge(args)

        project_a_experiments = list(experiments.load_all(project_a))

        assert len(project_a_experiments) == 1
        assert len(project_a_experiments[0]) == 3

        assert project_a_experiments[0][0]["finished"] is True
        assert project_a_experiments[0][1]["finished"] is True
        assert "finished" not in project_a_experiments[0][2]


def test_merge_source1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(
            ["merge", str(root_b), str(root_a), "--conflicts", "src"]
        )

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project_a.root)
        experiment_a.add_trial({"finished": True})
        experiment_a.add_trial({"finished": True})

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({})

        cli.merge.do_merge(args)

        project_a_experiments = list(experiments.load_all(project_a))

        assert len(project_a_experiments) == 1
        assert len(project_a_experiments[0]) == 2

        assert project_a_experiments[0][0]["finished"] is True
        assert "finished" not in project_a_experiments[0][1]


def test_merge_destination1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(
            ["merge", str(root_b), str(root_a), "--conflicts", "dst"]
        )

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project_a.root)
        experiment_a.add_trial({"finished": True})
        experiment_a.add_trial({})

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        cli.merge.do_merge(args)

        project_a_experiments = list(experiments.load_all(project_a))

        assert len(project_a_experiments) == 1
        assert len(project_a_experiments[0]) == 2

        assert project_a_experiments[0][0]["finished"] is True
        assert "finished" not in project_a_experiments[0][1]


def test_merge_keep_all_trials() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.merge.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as true_root:
        root_a = pathlib.Path(true_root) / "project_a"
        root_a.mkdir()
        project_a = projects.Project.new(root_a)

        root_b = pathlib.Path(true_root) / "project_b"
        root_b.mkdir()
        project_b = projects.Project.new(root_b)

        args = parser.parse_args(
            ["merge", str(root_b), str(root_a), "--conflicts", "keep"]
        )

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project_a.root)
        experiment_a.add_trial({"finished": True})
        experiment_a.add_trial({})

        experiment_b = experiments.Experiment.new({"file": "0.txt"}, project_b.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        cli.merge.do_merge(args)

        project_a_experiments = list(experiments.load_all(project_a))

        assert len(project_a_experiments) == 1
        assert len(project_a_experiments[0]) == 4

        assert project_a_experiments[0][0]["finished"] is True
        assert "finished" not in project_a_experiments[0][1]
        assert project_a_experiments[0][2]["finished"] is True
        assert project_a_experiments[0][3]["finished"] is True
