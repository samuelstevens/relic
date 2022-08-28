import pathlib
import tempfile

from relic import cli, experiments, projects


def test_make_experiment_fn1() -> None:
    filter_fn, needs_trials = cli.lib.shared.make_experiment_fn([])

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)

        experiment = experiments.Experiment.new({}, project.root)
        experiment.add_trial({})

        exps = list(experiments.load_all(project, filter_fn, needs_trials))

        assert len(exps) == 1


def test_make_experiment_fn2() -> None:
    filter_fn, needs_trials = cli.lib.shared.make_experiment_fn(
        ["(any (and (== succeeded False) (== finished True)))"]
    )

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)

        experiment = experiments.Experiment.new({}, project.root)
        experiment.add_trial({})

        exps = list(experiments.load_all(project, filter_fn, needs_trials))

        assert len(exps) == 0
