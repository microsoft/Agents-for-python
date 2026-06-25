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

from typing import Any

_TRUTHY = ("1", "true")
_FALSY = ("0", "false")


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
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is not None:
        text = str(value).strip().lower()
        if text in _TRUTHY:
            return True
        if text in _FALSY:
            return False
        if text:
            if default is not None:
                return default
            raise ValueError(f"Invalid boolean for {name}: {value!r}")
    # Unset (None or empty/whitespace-only string).
    if default is not None:
        return default
    raise ValueError(f"Invalid boolean for {name}: {value!r}")


def coerce_int(value: Any, default: int, name: str = "value") -> int:
    """Coerce a config value (possibly an env string) to an int.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset
    (a stray ``True``/``False`` is not a meaningful count). Numeric strings such
    as ``"5"`` or ``"5.0"`` are accepted; anything else raises ``ValueError``
    naming the offending setting.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(text, 10)
    except ValueError:
        try:
            return int(float(text))
        except ValueError as ex:
            raise ValueError(f"Invalid integer for {name}: {value!r}") from ex


def coerce_float(value: Any, default: float, name: str = "value") -> float:
    """Coerce a config value (possibly an env string) to a float.

    Empty/``None`` values fall back to ``default``. Bools are treated as unset.
    Anything that is not parseable as a float raises ``ValueError`` naming the
    offending setting.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError as ex:
        raise ValueError(f"Invalid number for {name}: {value!r}") from ex
