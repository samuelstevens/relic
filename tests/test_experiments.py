import copy
import pathlib
import tempfile

import pytest

from relic import experiments, projects


def test_smoke() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiments.Experiment.new(config={}, root=project.root)


def test_experiment_saves_on_new() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)


def test_hash_from_filepath() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        assert (
            experiment.hash_from_dir(experiment.directory(root, experiment.hash))
            == experiment.hash
        )

        assert (
            experiment.hash_from_dir(str(experiment.directory(root, experiment.hash)))
            == experiment.hash
        )


def test_load_from_filepath() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment_from_file = experiments.Experiment.load(
            project.root, experiment.hash
        )
        assert experiment_from_file == experiment


def test_load_missing_throws_error() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)

        hash = experiments.Experiment.hash_from_config({})

        with pytest.raises(experiments.Experiment.LoadError):
            experiments.Experiment.load(root, hash)


def test_load_corrupted_throws_error() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(experiment.root, experiment.hash)

        experiment.config_path(experiment.root, experiment.hash).unlink()

        with pytest.raises(experiments.Experiment.LoadError):
            experiments.Experiment.load(root, experiment.hash)


def test_delete_experiment() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.delete()
        assert not experiment.exists(root, experiment.hash)


def test_add_trial_smoke() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)


def test_add_trial_writes_to_disk() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)
        assert experiment.exists(experiment.root, experiment.hash)

        experiment_from_file = experiments.Experiment.load(
            project.root, experiment.hash
        )
        assert experiment_from_file == experiment


def test_add_trial_affects_length() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)
        experiment.add_trial({}, None)
        experiment.add_trial({}, None)
        assert len(experiment) == 3

        experiment_from_file = experiments.Experiment.load(
            project.root, experiment.hash
        )
        assert len(experiment_from_file) == 3


def test_add_trial_adds_instance_key() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)

        experiment = experiments.Experiment.new(config={}, root=root)
        assert experiment.exists(root, experiment.hash)

        experiment.add_trial({}, None)
        experiment.add_trial({}, None)
        experiment.add_trial({}, None)

        for i, trial in enumerate(experiment):
            assert i == trial["instance"]
            assert experiment[i] == trial


def test_add_trial_returns_with_instance_key() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)

        experiment = experiments.Experiment.new(config={}, root=root)
        assert experiment.exists(root, experiment.hash)

        trial = experiment.add_trial({}, None)
        assert len(experiment) == 1

        assert trial == {"instance": 0}


def test_add_existing_trial() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)

        experiment = experiments.Experiment.new(config={}, root=root)
        assert len(experiment) == 0

        experiment.add_trial({})
        assert len(experiment) == 1

        new_trial = {"a": 1, "instance": 0}

        with pytest.raises(AssertionError):
            experiment.add_trial(new_trial)


def test_add_trial_too_far() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)

        experiment = experiments.Experiment.new(config={}, root=root)
        assert len(experiment) == 0

        new_trial = {"a": 1, "instance": 1}

        with pytest.raises(AssertionError):
            experiment.add_trial(new_trial)


def test_delete_trials_smoke() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)
        assert len(experiment) == 1
        experiment.add_trial({}, None)
        assert len(experiment) == 2
        experiment.add_trial({}, None)
        assert len(experiment) == 3

        experiment.delete_trials()
        assert len(experiment) == 0


def test_delete_trials_writes_to_disk() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)
        assert len(experiment) == 1
        experiment.add_trial({}, None)
        assert len(experiment) == 2
        experiment.add_trial({}, None)
        assert len(experiment) == 3

        experiment_from_file_before_delete = experiments.Experiment.load(
            experiment.root, experiment.hash
        )

        experiment.delete_trials()

        experiment_from_file_with_no_trials = experiments.Experiment.load(
            experiment.root, experiment.hash
        )

        assert len(experiment) == 0
        assert len(experiment_from_file_before_delete) == 3
        assert len(experiment_from_file_with_no_trials) == 0


def test_update_trial_smoke() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)
        assert len(experiment) == 1

        new_trial = {"instance": 0, "a": "b"}

        experiment.update_trial(new_trial)
        assert experiment[0] == new_trial


def test_update_trial_adds_instance() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)
        assert len(experiment) == 1

        new_trial = {"a": 1, "instance": 0}

        experiment.update_trial(new_trial)
        assert experiment[0] == {**new_trial, "instance": 0}


def test_update_trial_modifies_disk() -> None:
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        experiment.add_trial({}, None)
        assert len(experiment) == 1

        new_trial = {"a": 1, "instance": 0}
        expected = copy.deepcopy(new_trial)

        actual = experiment.update_trial(new_trial)
        assert experiment[0] == expected
        assert actual == expected

        experiment_from_file = experiments.Experiment.load(
            project.root, experiment.hash
        )
        assert experiment_from_file == experiment
        assert experiment_from_file[0] == {**new_trial, "instance": 0}


def test_load_all() -> None:

    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)
        experiment = experiments.Experiment.new(config={}, root=project.root)
        assert experiment.exists(project.root, experiment.hash)

        exps = list(experiments.load_all(project))

        assert len(exps) == 1
        assert exps == [experiment]
