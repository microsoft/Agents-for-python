# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Callable, Mapping

from ._path.types._missing import _MISSING
from ._path import _Path, _get, _get_with_path, _try_set
from ._utils import _parse_env_var_name


def _path(*parts: str) -> str:
    return "::".join(parts)


def _default_path_transformer(parts: list[str]) -> _Path:
    return _Path.exact(
        *(
            segment
            for part in parts
            for segment in _parse_env_var_name(part).split("::")
        )
    )


def _validate_expanded_path(mapping: Mapping, path: _Path) -> None:
    if not isinstance(path, _Path):
        raise TypeError("path_transformer must return a _Path")
    for index, segment in enumerate(path):
        if not segment.string.isdecimal():
            continue
        _, matched_path = _get_with_path(mapping, path[: index + 1])
        if matched_path is not None and matched_path.last != segment.string:
            raise ValueError(
                f"Duplicate configuration list indices in path {path}: "
                f"{matched_path.last!r} and {segment.string!r}"
            )


def _expand_paths(
    source: Mapping, path_transformer: Callable[[list[str]], _Path]
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
            path_parts = parts + [str(key)]
            if isinstance(value, Mapping) and value:
                populate(value, path_parts)
                continue
            path = path_transformer(path_parts)
            _validate_expanded_path(expanded, path)
            existing = _get(expanded, path, default=_MISSING)
            if isinstance(value, Mapping) and isinstance(existing, Mapping):
                continue
            if not _try_set(expanded, path, copy_value(value)):
                raise ValueError(f"Conflicting configuration path {path}")

    populate(source, [])
    return expanded


def _normalize(
    source: Mapping, *, path_transformer: Callable[[list[str]], _Path]
) -> dict[str, Any]:
    """Expand paths and copy containers, normalizing indexed mappings to lists."""
    expanded = _expand_paths(source, path_transformer)

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
    path_transformer: Callable[[list[str]], _Path] | None = None,
) -> dict[str, Any]:
    """Normalize each source independently, then merge with primary precedence.

    The path transformer receives source key segments and returns a simple,
    nonempty ``_Path``. The default splits ``__`` and ``::`` separators while
    preserving case and single underscores. Values remain uncoerced, and the
    result contains ordinary dictionaries and lists owned by the resolver.
    """
    if path_transformer is None:
        path_transformer = _default_path_transformer
    base = _normalize(
        defaults if defaults is not None else {}, path_transformer=path_transformer
    )
    overrides = _normalize(primary, path_transformer=path_transformer)
    return _merge(base, overrides)
