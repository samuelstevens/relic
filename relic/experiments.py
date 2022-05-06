import dataclasses
import hashlib
import logging
import multiprocessing
import os
import pathlib
import shutil
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union, overload

import preface
import torch

from . import disk, json, projects, types

logger = logging.getLogger(__name__)

# https://discuss.pytorch.org/t/received-0-items-of-ancdata-pytorch-0-4-0/19823
torch.multiprocessing.set_sharing_strategy("file_system")  # type: ignore


class Trial(Dict[str, Any]):
    def __eq__(self, o: object) -> bool:
        if not isinstance(o, dict):
            return False

        if len(self) != len(o):
            return False

        for key in self:
            if key not in o:
                return False

            if isinstance(self[key], torch.Tensor) and isinstance(o[key], torch.Tensor):
                if not torch.equal(self[key], o[key]):
                    return False

            elif self[key] != o[key]:
                return False

        return True

    def __ne__(self, o: object) -> bool:
        return not (self == o)


@dataclasses.dataclass
class Experiment:
    hash: str
    root: pathlib.Path
    config: types.Config
    trials: List[Trial]

    def __post_init__(self) -> None:
        if not self.trials and self.exists(self.root, self.hash):
            obj = disk.load(self.file(self.root, self.hash))
            assert obj["trials"] == [], "logic error in relic!"
        else:
            for i, trial in enumerate(self.trials):
                if "instance" not in trial:
                    trial["instance"] = i
                else:
                    assert (
                        trial["instance"] == i
                    ), f"For experiment {self}, {trial['instance']} != {i}"

    @classmethod
    def new(cls, config: types.Config, root: pathlib.Path) -> "Experiment":
        hash = cls.hash_from_config(config)

        try:
            return cls.load(hash, root)
        except OSError:
            instance = cls(hash, root, config, [])
            instance.save()
            return instance

    class LoadError(Exception):
        err: Exception
        file: types.Path
        message: str

        def __init__(self, err: Exception, file: types.Path):
            self.err = err
            self.file = file
            self.message = f"File {file} is corrupted: {err}"

        def __str__(self) -> str:
            return self.message

    @classmethod
    def load(cls, hash: str, root: pathlib.Path) -> "Experiment":
        try:
            obj = disk.load(cls.file(root, hash))
        except EOFError as err:
            raise cls.LoadError(err, cls.file(root, hash))

        trials = [Trial(t) for t in obj["trials"]]
        return cls(hash, root, obj["config"], trials)

    def asdict(self) -> Dict[str, Any]:
        return {"config": self.config, "trials": self.trials}

    def save(self) -> None:
        disk.dump(self.file(self.root, self.hash), self.asdict())

    def delete(self) -> None:
        os.remove(self.file(self.root, self.hash))
        for i, _ in enumerate(self):
            self._delete_model(i)

    def _delete_model(self, trial: int) -> None:
        try:
            os.remove(self.model_path(trial))
        except FileNotFoundError:
            logger.info(
                "Couldn't delete model because it doesn't exist. [trial: %s, path: %s]",
                trial,
                self.model_path(trial),
            )

    def _add_model(self, trial: int, model_path: types.Path) -> pathlib.Path:
        """
        Copies a model from some location to the right location in the relics/ folder.
        """
        new_model_path = self.model_path(trial)
        os.makedirs(os.path.dirname(new_model_path), exist_ok=True)
        shutil.copy2(model_path, new_model_path)

        logger.info("Copied model. [from: %s, to: %s]", model_path, new_model_path)

        return new_model_path

    @staticmethod
    def file(root: pathlib.Path, hash: str) -> pathlib.Path:
        return root / (hash + ".relic")

    @staticmethod
    def hash_from_filepath(filepath: types.Path) -> str:
        if not isinstance(filepath, pathlib.Path):
            filepath = pathlib.Path(filepath)

        return filepath.stem

    @staticmethod
    def hash_from_config(config: types.Config) -> str:
        return hashlib.sha1(json.dumpb(config)).hexdigest()

    def add_trial(
        self, trial: Dict[str, Any], model_path: Optional[types.Path] = None
    ) -> Trial:
        if not isinstance(trial, Trial):
            trial = Trial(trial)

        if "instance" in trial:
            assert trial["instance"] == len(self)
        else:
            trial["instance"] = len(self)

        return self.update_trial(trial, model_path)

    def delete_trials(self, starting_from: int = 0) -> None:
        for i in range(starting_from, len(self)):
            self._delete_model(i)

        self.trials = self.trials[:starting_from]

        self.save()

    def update_trial(
        self, trial: Dict[str, Any], model_path: Optional[types.Path] = None
    ) -> Trial:
        if not isinstance(trial, Trial):
            trial = Trial(trial)

        assert "instance" in trial
        assert trial["instance"] <= len(self)

        if trial["instance"] < len(self):
            logger.debug(
                "Updating trial. [trial: %s, experiment trials: %s]",
                trial["instance"],
                len(self),
            )
            self[trial["instance"]] = trial
        else:
            logger.debug(
                "Adding trial. [trial: %s, experiment trials: %s]",
                trial["instance"],
                len(self),
            )
            assert trial["instance"] == len(self)
            self.trials.append(trial)

        if model_path is not None:
            self._add_model(trial["instance"], model_path)

        self.save()

        return trial

    @classmethod
    def exists(cls, root: pathlib.Path, hash: str) -> bool:
        return os.path.isfile(cls.file(root, hash))

    def model_path(self, trial: int) -> pathlib.Path:
        return self.root / "models" / self.hash / f"trial_{trial}.bin"

    def model_exists(self, trial: int) -> bool:
        return os.path.isfile(self.model_path(trial))

    def __len__(self) -> int:
        return len(self.trials)

    def __iter__(self) -> Iterator[Trial]:
        return iter(self.trials)

    def __str__(self) -> str:
        return self.hash

    @overload
    def __getitem__(self, key: int) -> Trial:
        ...

    @overload
    def __getitem__(self, key: slice) -> List[Trial]:
        ...

    def __getitem__(self, key: Union[int, slice]) -> Union[List[Trial], Trial]:
        return self.trials[key]

    def __setitem__(self, index: int, value: Trial) -> None:
        self.trials[index] = value

    def __hash__(self) -> int:
        return hash(self.hash)


def with_prefix(prefix: str, root: types.Path) -> Iterator[Experiment]:
    if not isinstance(root, pathlib.Path):
        root = pathlib.Path(root)

    for file in os.listdir(root):
        if Experiment.hash_from_filepath(file).startswith(prefix):
            yield Experiment.load(Experiment.hash_from_filepath(file), root)


def _load_experiment_safely(
    file: pathlib.Path, root: pathlib.Path
) -> Optional[Experiment]:
    try:
        return Experiment.load(Experiment.hash_from_filepath(file), root)
    except Experiment.LoadError as err:
        if os.path.getsize(err.file) == 0:
            return None
        raise err


def load_all(
    project: projects.Project,
    experiment_fn: types.FilterFn[Experiment] = lambda _: True,
) -> Iterator[Experiment]:
    """
    Generates an interator of experiments matching a filter function (experiment_fn).
    """
    assert callable(experiment_fn)

    path_and_roots = [(file, project.root) for file in project.experiment_files()]

    # Can't use context manager (with pool as ...) because of this issue with pytest coverage:
    # https://pytest-cov.readthedocs.io/en/latest/subprocess-support.html#if-you-use-multiprocessing-pool
    pool = multiprocessing.Pool()
    try:
        experiments = pool.starmap(
            _load_experiment_safely, path_and_roots, chunksize=32
        )
        for experiment in experiments:
            if experiment is not None and experiment_fn(experiment):
                yield experiment
    finally:
        pool.close()
        pool.join()


def _differing_fields(c1: types.Config, c2: types.Config) -> Iterator[str]:
    for key in c1:
        if key not in c2:
            yield key
            continue
        # now the key is both c

        if not isinstance(c1[key], type(c2[key])) or not isinstance(
            c2[key], type(c1[key])
        ):
            yield key
            continue

        # now they're the same type
        if c1[key] != c2[key]:
            yield key
            continue


def differing_config_fields(exps: Sequence[Experiment]) -> List[str]:
    fields = set()
    for e1, e2 in zip(exps, exps[1:]):
        config1 = preface.dict.flattened(e1.config)
        config2 = preface.dict.flattened(e2.config)
        fields |= set(_differing_fields(config1, config2))
        fields |= set(_differing_fields(config2, config1))

    return list(sorted(fields))
