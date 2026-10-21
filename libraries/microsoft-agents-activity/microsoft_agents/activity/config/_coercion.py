# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Coercion helpers for values loaded from environment configuration.

:func:`load_configuration_from_env` keeps every value as the raw string (or a
nested ``dict``) read from the environment. Consumers that expect a bool, int or
float must coerce explicitly: a naive ``bool("false")`` is ``True`` and would
silently invert a flag, and ``int("5") + 1`` style math fails on values that may
legitimately arrive as strings. These helpers centralize that coercion so every
config consumer parses env values the same, fail-safe way.
"""

from __future__ import annotations

from typing import (
    Any,
    Mapping,
    overload,
)

from ._utils import (
    _MISSING,
    _MISSING_CLS,
    _get,
    _is_missing,
)

_TRUTHY = ("1", "true")
_FALSY = ("0", "false")

@overload
def _handle_bool(value: Any, default: bool | None = None, name: str = "value") -> bool | None:
    ...
@overload
def _handle_bool(value: Any, default: bool | _MISSING_CLS = _MISSING, name: str = "value") -> bool:
    ...
def _handle_bool(value: Any, default: bool | None | _MISSING_CLS = None, name: str = "value") -> bool | None:
    """Coerce a config value (possibly an env string) to a bool.

    Environment variables always arrive as strings, so ``bool("false")`` would
    be ``True``. Recognized truthy spellings are ``1/true`` and falsy spellings
    are ``0/false`` (case-insensitive).

    An empty/whitespace-only string or ``None`` is treated as *unset* (not as an
    explicit ``false``). For unset and unrecognized values: if ``default`` is
    provided it is returned, otherwise a ``ValueError`` is raised naming the
    offending setting -- mirroring :func:`coerce_int` and :func:`coerce_float`.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is not None and not _is_missing(value):
        text = str(value).strip().lower()
        if text in _TRUTHY:
            return True
        if text in _FALSY:
            return False
        if text:
            raise ValueError(f"Invalid boolean for {name}: {value!r}")
    if _is_missing(default):
        raise ValueError(f"Missing boolean for {name}: {value!r}")
    return default
    
def coerce_bool(value: Any, default: bool | None = None, name: str = "value") -> bool:
    """Coerce a config value (possibly an env string) to a bool.

    Environment variables always arrive as strings, so ``bool("false")`` would
    be ``True``. Recognized truthy spellings are ``1/true`` and falsy spellings
    are ``0/false`` (case-insensitive).

    An empty/whitespace-only string or ``None`` is treated as *unset* (not as an
    explicit ``false``). For unset and unrecognized values: if ``default`` is
    provided it is returned, otherwise a ``ValueError`` is raised naming the
    offending setting -- mirroring :func:`coerce_int` and :func:`coerce_float`.
    """
    new_default = default if default is not None else _MISSING
    return _handle_bool(value, new_default, name)

@overload
def _handle_int(value: Any, default: int | _MISSING_CLS = _MISSING, name: str = "value") -> int:
    ...
@overload
def _handle_int(value: Any, default: int | None = None, name: str = "value") -> int | None:
    ...
def _handle_int(value: Any, default: int | None | _MISSING_CLS = None, name: str = "value") -> int | None:
    """Coerce a config value (possibly an env string) to an int.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset
    (a stray ``True``/``False`` is not a meaningful count). Numeric strings such
    as ``"5"`` or ``"5.0"`` are accepted; anything else raises ``ValueError``
    naming the offending setting.
    """
    if value is None or _is_missing(value):
        if _is_missing(default):
            raise ValueError(f"Missing integer for {name}: {value!r}")
        return default
    if isinstance(value, bool):
        if _is_missing(default):
            raise ValueError(f"Missing integer for {name}: {value!r}")
        return default # TODO -> should this raise?
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        if _is_missing(default):
            raise ValueError(f"Missing integer for {name}: {value!r}")
        return default
    try:
        return int(text, 10)
    except ValueError:
        try:
            return int(float(text))
        except ValueError as ex:
            raise ValueError(f"Invalid integer for {name}: {value!r}") from ex

def coerce_int(value: Any, default: int | None = None, name: str = "value") -> int:
    """Coerce a config value (possibly an env string) to an int.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset
    (a stray ``True``/``False`` is not a meaningful count). Numeric strings such
    as ``"5"`` or ``"5.0"`` are accepted; anything else raises ``ValueError``
    naming the offending setting.
    """
    new_default = default if default is not None else _MISSING
    return _handle_int(value, new_default, name)

@overload
def _handle_float(value: Any, default: float | _MISSING_CLS, name: str = "value") -> float:
    ...
@overload
def _handle_float(value: Any, default: float | None = None, name: str = "value") -> float | None:
    ...
def _handle_float(value: Any, default: float | None | _MISSING_CLS = None, name: str = "value") -> float | None:
    """Coerce a config value (possibly an env string) to a float.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset.
    Anything that is not parseable as a float raises ``ValueError`` naming the
    offending setting.
    """
    if value is None or _is_missing(value):
        if _is_missing(default):
            raise ValueError(f"Missing number for {name}: {value!r}")
        return default
    if isinstance(value, bool):
        if _is_missing(default):
            raise ValueError(f"Missing number for {name}: {value!r}")
        return default # TODO -> should this also raise?
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        if _is_missing(default):
            raise ValueError(f"Missing number for {name}: {value!r}")
        return default
    try:
        return float(text)
    except ValueError as ex:
        raise ValueError(f"Invalid number for {name}: {value!r}") from ex

def coerce_float(value: Any, default: float | None = None, name: str = "value") -> float:
    """Coerce a config value (possibly an env string) to a float.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset.
    Anything that is not parseable as a float raises ``ValueError`` naming the
    offending setting.
    """
    new_default = default if default is not None else _MISSING
    return _handle_float(value, new_default, name)

def _check_key_error(value: Any, default: Any, key: str) -> None:
    if _is_missing(value) and _is_missing(default):
        raise KeyError(key)

@overload
def _handle_str(value: Any, default: str | None = None, name: str = "value") -> str | None:
    ...
@overload
def _handle_str(value: Any, default: str | _MISSING_CLS = _MISSING, name: str = "value") -> str:
    ...
def _handle_str(value: Any, default: str | None | _MISSING_CLS = None, name: str = "value") -> str | None:
    if value is None or _is_missing(value):
        if _is_missing(default):
            raise ValueError(f"Missing string for {name}: {value!r}")
        return default
    if isinstance(value, str):
        return value
    return str(value)

@overload
def _get_bool(mapping: Mapping, key: str, default: bool | _MISSING_CLS) -> bool:
    ...
@overload
def _get_bool(mapping: Mapping, key: str, default: bool | None) -> bool | None:
    ...
def _get_bool(mapping: Mapping, key: str, default: bool | None | _MISSING_CLS = _MISSING) -> bool | None:
    val = _get(mapping, key, _MISSING)
    _check_key_error(val, default, key)
    return _handle_bool(val, default, key)

@overload
def _get_int(mapping: Mapping, key: str, default: int | _MISSING_CLS) -> int:
    ...
@overload
def _get_int(mapping: Mapping, key: str, default: int | None) -> int | None:
    ...
def _get_int(mapping: Mapping, key: str, default: int | None | _MISSING_CLS = _MISSING) -> int | None:
    val = _get(mapping, key, _MISSING)
    _check_key_error(val, default, key)
    return _handle_int(val, default, key)

@overload
def _get_float(mapping: Mapping, key: str, default: float | _MISSING_CLS) -> float:
    ...
@overload
def _get_float(mapping: Mapping, key: str, default: float | None) -> float | None:
    ...
def _get_float(mapping: Mapping, key: str, default: float | None | _MISSING_CLS = _MISSING) -> float | None:
    val = _get(mapping, key, _MISSING)
    _check_key_error(val, default, key)
    return _handle_float(val, default, key)

@overload
def _get_str(mapping: Mapping, key: str, default: str | _MISSING_CLS) -> str:
    ...
@overload
def _get_str(mapping: Mapping, key: str, default: str | None) -> str | None:
    ...
def _get_str(mapping: Mapping, key: str, default: str | None | _MISSING_CLS = _MISSING) -> str | None:
    val = _get(mapping, key, _MISSING)
    _check_key_error(val, default, key)
    return _handle_str(val, default, key)