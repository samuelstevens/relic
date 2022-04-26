import pathlib
import tempfile

from relic import cli, experiments, projects


def test_find_natural_n_experiments() -> None:
    filter_fn = cli.lib.shared.make_experiment_fn(
        ["(== training.batch_size 16)", "(== training.optimizer 'AdamW')"]
    )
    with tempfile.TemporaryDirectory() as root_name:
        root = pathlib.Path(root_name)
        project = projects.Project.new(root)

        expected_exps = set(
            [
                experiments.Experiment.new(
                    {"training": {"batch_size": 16, "optimizer": "AdamW"}},
                    project.root,
                ),
                experiments.Experiment.new(
                    {
                        "training": {"batch_size": 16, "optimizer": "AdamW"},
                        "data": {
                            "file": "data/random-words/2-chunks/0.txt",
                            "prompt_type": "uuid",
                        },
                    },
                    project.root,
                ),
                experiments.Experiment.new(
                    {
                        "training": {"batch_size": 16, "optimizer": "AdamW"},
                        "data": {"file": "data/reddit/0.txt", "prompt_type": "chunk-n"},
                    },
                    project.root,
                ),
            ]
        )

        actual_exps = set(experiments.load_all(project, filter_fn))

        assert actual_exps == expected_exps
