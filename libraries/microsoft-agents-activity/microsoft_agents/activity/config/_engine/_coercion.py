# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Typed conversion for raw configuration values.

Loading and wrapping configuration do not coerce scalar values. These helpers
let typed consumers distinguish missing/unset values from invalid input without
relying on Python truthiness, where ``bool("false")`` would incorrectly be True.
"""

from __future__ import annotations

from typing import (
    Any,
    Mapping,
    overload,
)

from ._path.types._missing import _MISSING, _MissingType, _is_missing
from ._path import _get, _Path, _PathProxy

_TRUTHY = ("1", "true")
_FALSY = ("0", "false")


@overload
def _handle_bool(
    value: Any, default: None = None, name: str | _Path = "value"
) -> bool | None: ...
@overload
def _handle_bool(
    value: Any, default: bool | _MissingType = _MISSING, name: str | _Path = "value"
) -> bool: ...
def _handle_bool(
    value: Any, default: bool | None | _MissingType = None, name: str | _Path = "value"
) -> bool | None:
    """Coerce a config value (possibly an env string) to a bool.

    Environment variables always arrive as strings, so ``bool("false")`` would
    be ``True``. Recognized truthy spellings are ``1/true`` and falsy spellings
    are ``0/false`` (case-insensitive).

    An empty/whitespace-only string or ``None`` is treated as *unset* (not as an
    explicit ``false``). Unset values return the default, or raise if no default
    was supplied. Unrecognized nonempty values always raise ``ValueError``.
    Errors identify the setting without including its input value.
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
            raise ValueError(f"Invalid boolean for {str(name)}")
    if _is_missing(default):
        raise ValueError(f"Missing boolean for {str(name)}")
    return default


def coerce_bool(value: Any, default: bool | None = None, name: str = "value") -> bool:
    """Convert one value to a boolean, without looking up a configuration key.

    Accept ``"true"``/``"1"`` and ``"false"``/``"0"``, ignoring case and
    surrounding whitespace. Unlike Python's ``bool("false")``, this reads the
    string ``"false"`` as False.

    Missing, blank, or unrecognized values return a supplied True/False default;
    otherwise they raise ``ValueError``. Unlike ``Configuration.get_bool``, this
    helper also uses its default for invalid nonempty text.

    Example::

        >>> from microsoft_agents.activity.config import coerce_bool
        >>> coerce_bool("false")
        False
        >>> coerce_bool("not a boolean", default=False)
        False

    :param value: Value to convert.
    :param default: Boolean to use if conversion is not possible.
    :param name: Setting name to include in error messages, without its value.
    """
    new_default = default if default is not None else _MISSING
    try:
        return _handle_bool(value, new_default, name)
    except ValueError:
        if default is not None:
            return default
        raise


@overload
def _handle_int(
    value: Any, default: int | _MissingType = _MISSING, name: str | _Path = "value"
) -> int: ...
@overload
def _handle_int(
    value: Any, default: None = None, name: str | _Path = "value"
) -> int | None: ...
def _handle_int(
    value: Any, default: int | None | _MissingType = None, name: str | _Path = "value"
) -> int | None:
    """Coerce a config value (possibly an env string) to an int.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset
    (a stray ``True``/``False`` is not a meaningful count). Numeric strings such
    as ``"5"`` or ``"5.0"`` are accepted; anything else raises ``ValueError``
    naming the offending setting.
    """
    if value is None or _is_missing(value):
        if _is_missing(default):
            raise ValueError(f"Missing integer for {str(name)}")
        return default
    if isinstance(value, bool):
        if _is_missing(default):
            raise ValueError(f"Missing integer for {str(name)}")
        return default  # TODO -> should this raise?
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        if _is_missing(default):
            raise ValueError(f"Missing integer for {str(name)}")
        return default
    try:
        return int(text, 10)
    except ValueError:
        try:
            return int(float(text))
        except ValueError:
            raise ValueError(f"Invalid integer for {str(name)}") from None


def coerce_int(value: Any, default: int | None = None, name: str = "value") -> int:
    """Convert one value to an integer, without looking up a configuration key.

    Accept numbers and numeric strings such as ``"5"`` or ``"5.9"``, discarding
    fractional parts. Blank values, ``None``, and booleans use a supplied
    default, or raise ``ValueError`` without one. Invalid nonempty text always
    raises ``ValueError``.

    Example::

        >>> from microsoft_agents.activity.config import coerce_int
        >>> coerce_int("5")
        5
        >>> coerce_int(None, default=3)
        3

    :param value: Value to convert.
    :param default: Integer to use for a missing or blank value.
    :param name: Setting name to include in error messages, without its value.
    """
    new_default = default if default is not None else _MISSING
    return _handle_int(value, new_default, name)


@overload
def _handle_float(
    value: Any, default: float | _MissingType, name: str | _Path = "value"
) -> float: ...
@overload
def _handle_float(
    value: Any, default: None = None, name: str | _Path = "value"
) -> float | None: ...
def _handle_float(
    value: Any, default: float | None | _MissingType = None, name: str | _Path = "value"
) -> float | None:
    """Coerce a config value (possibly an env string) to a float.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset.
    Anything that is not parseable as a float raises ``ValueError`` naming the
    offending setting.
    """
    if value is None or _is_missing(value):
        if _is_missing(default):
            raise ValueError(f"Missing number for {str(name)}")
        return default
    if isinstance(value, bool):
        if _is_missing(default):
            raise ValueError(f"Missing number for {str(name)}")
        return default  # TODO -> should this also raise?
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        if _is_missing(default):
            raise ValueError(f"Missing number for {str(name)}")
        return default
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"Invalid number for {str(name)}") from None


def coerce_float(
    value: Any, default: float | None = None, name: str = "value"
) -> float:
    """Convert one value to a float, without looking up a configuration key.

    Blank values, ``None``, and booleans use a supplied default, or raise
    ``ValueError`` without one. Invalid nonempty text always raises
    ``ValueError``.

    Example::

        >>> from microsoft_agents.activity.config import coerce_float
        >>> coerce_float("0.5")
        0.5
        >>> coerce_float(None, default=1.0)
        1.0

    :param value: Value to convert.
    :param default: Number to use for a missing or blank value.
    :param name: Setting name to include in error messages, without its value.
    """
    new_default = default if default is not None else _MISSING
    return _handle_float(value, new_default, name)


def _check_key_error(value: Any, default: Any, key: str) -> None:
    if _is_missing(value) and _is_missing(default):
        raise KeyError(key)


@overload
def _handle_str(
    value: Any, default: None = None, name: str | _Path = "value"
) -> str | None: ...
@overload
def _handle_str(
    value: Any, default: str | _MissingType = _MISSING, name: str | _Path = "value"
) -> str: ...
def _handle_str(
    value: Any, default: str | None | _MissingType = None, name: str | _Path = "value"
) -> str | None:
    if value is None or _is_missing(value):
        if _is_missing(default):
            raise ValueError(f"Missing string for {str(name)}")
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _handle_str_list(
    value: Any, default: list[str] | None = None, name: str | _Path = "value"
) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{str(name)} must be a list.")
    values = [_handle_str(val) for val in value]
    return [val for val in values if val is not None]


@overload
def _get_bool(
    mapping: Mapping, _path: _PathProxy, default: bool | _MissingType
) -> bool: ...
@overload
def _get_bool(mapping: Mapping, _path: _PathProxy, default: None) -> bool | None: ...
def _get_bool(
    mapping: Mapping, _path: _PathProxy, default: bool | None | _MissingType = _MISSING
) -> bool | None:
    path = _Path.create(_path)
    val = _get(mapping, path, default=_MISSING)
    _check_key_error(val, default, path.last)
    return _handle_bool(val, default, path)


@overload
def _get_int(
    mapping: Mapping, _path: _PathProxy, default: int | _MissingType
) -> int: ...
@overload
def _get_int(mapping: Mapping, _path: _PathProxy, default: None) -> int | None: ...
def _get_int(
    mapping: Mapping, _path: _PathProxy, default: int | None | _MissingType = _MISSING
) -> int | None:
    path = _Path.create(_path)
    val = _get(mapping, path, default=_MISSING)
    _check_key_error(val, default, path.last)
    return _handle_int(val, default, path)


@overload
def _get_float(
    mapping: Mapping, _path: _PathProxy, default: float | _MissingType
) -> float: ...
@overload
def _get_float(mapping: Mapping, _path: _PathProxy, default: None) -> float | None: ...
def _get_float(
    mapping: Mapping, _path: _PathProxy, default: float | None | _MissingType = _MISSING
) -> float | None:
    path = _Path.create(_path)
    val = _get(mapping, path, default=_MISSING)
    _check_key_error(val, default, path.last)
    return _handle_float(val, default, path)


@overload
def _get_str(
    mapping: Mapping, _path: _PathProxy, default: str | _MissingType
) -> str: ...
@overload
def _get_str(mapping: Mapping, _path: _PathProxy, default: None) -> str | None: ...
def _get_str(
    mapping: Mapping, _path: _PathProxy, default: str | None | _MissingType = _MISSING
) -> str | None:
    path = _Path.create(_path)
    val = _get(mapping, path, default=_MISSING)
    _check_key_error(val, default, path.last)
    return _handle_str(val, default, path)
