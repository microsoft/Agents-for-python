# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Callable, Mapping

from ._utils import _MISSING, _get, _parse_env_var_name, _path, _try_set


def _expand_paths(
    source: Mapping, path_transformer: Callable[[str], str]
) -> dict[str, Any]:
    expanded: dict[str, Any] = {}

    def copy_value(value: Any) -> Any:
        if isinstance(value, Mapping):
            return _expand_paths(value, path_transformer)
        if isinstance(value, list):
            return [copy_value(item) for item in value]
        return value

    def populate(mapping: Mapping, parts: list[str]) -> None:
        for key, value in mapping.items():
            if not isinstance(key, (str, int)):
                raise TypeError("Configuration keys must be strings or integers")
            path = parts + [str(key)]
            if isinstance(value, Mapping) and value:
                populate(value, path)
                continue
            name = path_transformer(_path(*path))
            existing = _get(expanded, name, default=_MISSING)
            if isinstance(value, Mapping) and isinstance(existing, Mapping):
                continue
            if not _try_set(expanded, name, copy_value(value)):
                raise ValueError(f"Conflicting configuration path {name}")

    populate(source, [])
    return expanded


def _normalize(
    source: Mapping, *, path_transformer: Callable[[str], str] | None = None
) -> dict[str, Any]:
    """Expand paths and copy containers, normalizing indexed mappings to lists."""
    transform = path_transformer or _parse_env_var_name
    expanded = _expand_paths(source, transform)

    def convert(value: Any) -> Any:
        if isinstance(value, dict):
            converted = {key: convert(item) for key, item in value.items()}
            if converted and all(key.isdecimal() for key in converted):
                indices = sorted(converted, key=int)
                if len({int(key) for key in indices}) != len(indices):
                    raise ValueError("Duplicate configuration list indices")
                return [converted[key] for key in indices]
            return converted
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    return {key: convert(value) for key, value in expanded.items()}


def _merge(
    defaults: dict[str, Any],
    primary: dict[str, Any],
    *,
    _base_path: str = "",
) -> dict[str, Any]:
    """Merge owned mappings in place; primary lists replace default lists."""
    for key, value in primary.items():
        if key not in defaults:
            defaults[key] = value
            continue
        previous = defaults[key]
        name = _path(_base_path, key) if _base_path else key
        if isinstance(previous, dict) and isinstance(value, dict):
            _merge(previous, value, _base_path=name)
        elif isinstance(previous, dict) or isinstance(value, dict):
            raise TypeError(f"Conflicting configuration structure at {name}")
        else:
            defaults[key] = value
    return defaults


def _resolve(
    primary: Mapping,
    defaults: Mapping | None = None,
    *,
    path_transformer: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Normalize each source independently, then merge with primary precedence."""
    base = _normalize(
        defaults if defaults is not None else {}, path_transformer=path_transformer
    )
    overrides = _normalize(primary, path_transformer=path_transformer)
    return _merge(base, overrides)
