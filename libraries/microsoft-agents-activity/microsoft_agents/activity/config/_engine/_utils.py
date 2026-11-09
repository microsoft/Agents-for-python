# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools

from typing import Any, Callable, Mapping, MutableMapping, TypeVar
from typing_extensions import TypeIs

from .._constants import _PATH_SEPARATOR, _PATH_ANY
from ._path import _Path
from ._path._utils import (
    _get_with_path,
    _get,
    _collect_with_paths,
    _collect,
    _try_set,
    _set,
)

T = TypeVar("T")

def _xpath(*segments: str) -> _Path:
    return _Path.from_strings(*segments, ignore_case=True)

def _parse_env_var_name(name: str) -> str:
    """Replace environment-variable ``__`` separators with ``::``.

    :param name: The environment variable name.
    :return: The ``::``-separated key path, preserving case.
    """
    return name.replace("__", _PATH_SEPARATOR)

def str_in(base: str, *sub: str) -> bool:
    """Check if any of the given substrings are present in the base string.

    :param base: The base string.
    :param sub: Substrings to check for.
    :return: True if any of the substrings are present in the base string, False otherwise.
    """
    return any(s in base for s in sub)

def _resolve_path(path: str | list[str] | _Path) -> _Path:
    if isinstance(path, _Path):
        return path
    if isinstance(path, str):
        return _Path.from_strings(path)
    if isinstance(path, list):
        return _Path.from_strings(*path)
    raise ValueError(f"Invalid path type: {type(path)}")


def _resolve_keys_arg(*keys: str | list[str]) -> list[str]:
    resolved_keys = []
    for key in keys:
        if isinstance(key, str):
            resolved_keys.append(key)
        elif isinstance(key, list):
            resolved_keys.extend(key)
        else:
            raise ValueError(f"Invalid key type: {type(key)}")
    return resolved_keys