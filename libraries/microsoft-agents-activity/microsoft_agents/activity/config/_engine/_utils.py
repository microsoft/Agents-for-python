# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import TypeVar

T = TypeVar("T")

def _parse_env_var_name(name: str) -> str:
    """Replace environment-variable ``__`` separators with ``::``.

    :param name: The environment variable name.
    :return: The ``::``-separated key path, preserving case.
    """
    return name.replace("__", "::")

def str_in(base: str, *sub: str) -> bool:
    """Check if any of the given substrings are present in the base string.

    :param base: The base string.
    :param sub: Substrings to check for.
    :return: True if any of the substrings are present in the base string, False otherwise.
    """
    return any(s in base for s in sub)

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