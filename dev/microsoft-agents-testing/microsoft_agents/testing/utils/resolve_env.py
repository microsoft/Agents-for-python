from glob import glob
from pathlib import Path

from dotenv import dotenv_values


def resolve_env(path: str | Path) -> dict:
    """Resolves a .env file from a given path, which can be a file or directory.

    :param path: Path to a .env file or a directory containing a .env file.
    :return: A dictionary containing the key-value pairs from the .env file.
    """

    path = Path(path)

    if path.is_dir():
        env_files = glob(str(path / ".env"))
        if not env_files:
            raise FileNotFoundError(f"No .env file found in directory: {path}")
        path = Path(env_files[0])

    config = dotenv_values(path)
    return config
