"""
Migrates relics from v1 to v2 (performance optimization).
"""

import shutil
import pathlib
import torch
import pickle

OLD_RELICS = pathlib.Path("relics-old")
RELICS = pathlib.Path("relics")


def read(path):
    obj = torch.load(path)
    breakpoint()


def main():
    # Move relics to relics-old
    shutil.move(RELICS, OLD_RELICS)

    for version in OLD_RELICS.iterdir():
        if not (OLD_RELICS / version).is_dir():
            assert version == "project.json"

            shutil.copy(OLD_RELICS / version, RELICS / version)
        else:
            assert version.startswith("v")

            for hash in (OLD_RELICS / version).iterdir():
                if (OLD_RELICS / version / hash).is_dir():
                    assert hash == "models"
                    continue

                (RELICS / version / hash).mkdir(parents=True)
                (RELICS / version / hash / "trials").mkdir()

                shutil.copy(
                    OLD_RELICS / version / "models" / hash,
                    RELICS / version / hash / "models",
                )

                for m, model in enumerate(
                    sorted((RELICS / version / hash / "models").iterdir())
                ):
                    shutil.move(
                        RELICS / version / hash / "models" / model,
                        RELICS / version / hash / "models" / f"{m}.model",
                    )

                config, trials = read(OLD_RELICS / version / hash)

                torch.save(
                    config,
                    RELICS / version / hash / "config",
                    pickle_protocol=pickle.HIGHEST_PROTOCOL,
                )

                for t, trial in enumerate(trials):
                    torch.save(
                        trial,
                        RELICS / version / hash / "trials" / f"{t}.trial",
                        pickle_protocol=pickle.HIGHEST_PROTOCOL,
                    )


if __name__ == "__main__":
    main()
