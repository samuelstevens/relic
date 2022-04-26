import argparse
import pathlib
import tempfile

from relic import cli, experiments, projects


def test_delete_hashes1() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.delete.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as rootname:
        root = pathlib.Path(rootname)
        project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project.root)
        experiment_a.add_trial({"finished": True})

        experiment_b = experiments.Experiment.new({"file": "1.txt"}, project.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        args = parser.parse_args(["delete", "--hashes", experiment_a.hash[:10]])
        args.project = projects.Project(root)

        before = list(experiments.load_all(project))
        assert len(before) == 2

        cli.delete.do_delete(args)
        remaining = list(experiments.load_all(project))

        assert len(remaining) == 1
        assert remaining[0] == experiment_b


def test_delete_hashes2() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.delete.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as rootname:
        root = pathlib.Path(rootname)
        project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project.root)
        experiment_a.add_trial({"finished": True})

        experiment_b = experiments.Experiment.new({"file": "1.txt"}, project.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        args = parser.parse_args(["delete", "--hashes", experiment_b.hash[:10]])
        args.project = projects.Project(root)

        before = list(experiments.load_all(project))
        assert len(before) == 2

        cli.delete.do_delete(args)
        remaining = list(experiments.load_all(project))

        assert len(remaining) == 1
        assert remaining[0] == experiment_a


def test_delete_hashes_no_matches() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.delete.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as rootname:
        root = pathlib.Path(rootname)
        project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project.root)
        experiment_a.add_trial({"finished": True})

        experiment_b = experiments.Experiment.new({"file": "1.txt"}, project.root)
        experiment_b.add_trial({"finished": True})
        experiment_b.add_trial({"finished": True})

        args = parser.parse_args(["delete", "--hashes", "lmno"])
        args.project = projects.Project(root)

        before = list(experiments.load_all(project))
        assert len(before) == 2

        returncode = cli.delete.do_delete(args)
        assert returncode != 0

        remaining = list(experiments.load_all(project))

        assert len(remaining) == 2
        assert set(remaining) == {experiment_a, experiment_b}


def test_delete_hashes_more_than_one_match() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.delete.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as rootname:
        root = pathlib.Path(rootname)
        project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project.root)
        experiment_a.add_trial({"finished": True})

        experiment_b = experiments.Experiment.new({"file": "1.txt"}, project.root)
        experiment_b.add_trial({"finished": True})

        experiment_c = experiments.Experiment.new({"file": "2.txt"}, project.root)
        experiment_c.add_trial({"finished": True})

        experiment_d = experiments.Experiment.new({"file": "3.txt"}, project.root)
        experiment_d.add_trial({"finished": True})

        experiment_e = experiments.Experiment.new({"file": "4.txt"}, project.root)
        experiment_e.add_trial({"finished": True})

        experiment_f = experiments.Experiment.new({"file": "5.txt"}, project.root)
        experiment_f.add_trial({"finished": True})

        experiment_g = experiments.Experiment.new({"file": "6.txt"}, project.root)
        experiment_g.add_trial({"finished": True})

        # d and g have the same prefix
        args = parser.parse_args(["delete", "--hashes", "1"])
        args.project = projects.Project(root)

        before = list(experiments.load_all(project))
        assert len(before) == 7

        returncode = cli.delete.do_delete(args)
        assert returncode != 0

        remaining = list(experiments.load_all(project))

        assert len(remaining) == 7


def test_delete_experiment_filter_fn() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli.delete.add_parser(subparsers)

    with tempfile.TemporaryDirectory() as rootname:
        root = pathlib.Path(rootname)
        project = projects.Project.new(root)

        experiment_a = experiments.Experiment.new({"file": "0.txt"}, project.root)
        experiment_a.add_trial({"finished": True})

        experiment_b = experiments.Experiment.new({"file": "1.txt"}, project.root)
        experiment_b.add_trial({"finished": True})

        experiment_c = experiments.Experiment.new({"file": "2.txt"}, project.root)
        experiment_c.add_trial({"finished": True})

        args = parser.parse_args(["delete", "--experiments", "(== file '2.txt')"])
        args.project = projects.Project(root)

        before = list(experiments.load_all(project))
        assert len(before) == 3

        returncode = cli.delete.do_delete(args)
        assert returncode == 0

        remaining = list(experiments.load_all(project))

        assert len(remaining) == 2
