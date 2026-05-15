"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple


def _parse_path(path: str) -> Optional[list[Any]]:
    """Tokenize a dot/bracket path into a list of segments.

    Supports ``a.b.c``, ``a[0].b``, ``a[1][2]``. Integer brackets become ``int``
    segments; everything else becomes a string segment. Returns ``None`` for
    malformed bracket nesting.
    """
    if not path:
        return []

    segments: list[Any] = []
    i = 0
    start = 0

    def emit() -> None:
        nonlocal start
        if start < i:
            segments.append(path[start:i])
        start = i + 1

    while i < len(path):
        ch = path[i]
        if ch == ".":
            emit()
        elif ch == "[":
            emit()
            nesting = 1
            i += 1
            inner_start = i
            while i < len(path):
                c = path[i]
                if c == "[":
                    nesting += 1
                elif c == "]":
                    nesting -= 1
                    if nesting == 0:
                        break
                i += 1
            if nesting != 0:
                return None
            inner = path[inner_start:i]
            if inner.isdigit() or (inner.startswith("-") and inner[1:].isdigit()):
                segments.append(int(inner))
            else:
                segments.append(inner)
            start = i + 1
        i += 1

    emit()
    return segments


def _resolve_segment(current: Any, segment: Any) -> Tuple[bool, Any]:
    """Resolve one path segment against the current node.

    Returns ``(found, value)``. ``found`` is False when the segment cannot be
    resolved (missing key, out-of-range index, primitive node).
    """
    if current is None:
        return False, None

    if isinstance(segment, int):
        if isinstance(current, (list, tuple)):
            if -len(current) <= segment < len(current):
                return True, current[segment]
            return False, None
        return False, None

    # string segment → dict key (case-sensitive fast path, case-insensitive fallback)
    if isinstance(current, dict):
        if segment in current:
            return True, current[segment]
        lower = segment.lower()
        for key, value in current.items():
            if isinstance(key, str) and key.lower() == lower:
                return True, value
        return False, None

    return False, None


def try_get_path_value(data: Any, path: str) -> Tuple[bool, Any]:
    """Walk ``path`` against ``data``. Returns ``(found, value)``."""
    if data is None:
        return False, None
    if not path:
        return True, data

    segments = _parse_path(path)
    if segments is None:
        return False, None

    current: Any = data
    for segment in segments:
        found, current = _resolve_segment(current, segment)
        if not found:
            return False, None
    return True, current
