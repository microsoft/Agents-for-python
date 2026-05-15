"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict

from .._path_navigator import try_get_path_value

T = TypeVar("T")


class SlackModel(BaseModel):
    """
    Base class for Slack model objects that expose dot-notation path navigation via
    :meth:`get` and :meth:`try_get`.

    Subclasses are Pydantic models with ``extra="allow"`` so any unmodelled fields
    from Slack are preserved and reachable by path. The path navigator walks the
    serialized form (``by_alias=True``), so paths use the same snake_case names
    that appear in the Slack docs.

    Subclasses whose JSON field names differ from their Python property names
    override :meth:`_normalize_path` to remap the alias before navigation (e.g.
    :class:`EventEnvelope` maps ``event_content`` → ``event``).
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def _data(self) -> dict[str, Any]:
        """Return the serialized form used for path navigation. Subclasses with
        their own backing store may override this."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=False)

    def _normalize_path(self, path: str) -> str:
        """Remap caller-supplied path before navigation. Default: identity."""
        return path

    def get(self, path: str, default: Optional[T] = None, type_: Type[T] = None) -> Any:
        """Get a value at the dot-notation ``path``. Supports dot separators and
        bracket array indexing (e.g. ``"message.attachments[0].text"``). Returns
        ``default`` (or ``None``) when the path does not exist.

        ``type_`` is accepted for API symmetry with the C# generic ``Get<T>`` but
        is not enforced at runtime — Pydantic models keep values in their
        deserialized shape.
        """
        if not path:
            return self._data()

        found, value = try_get_path_value(self._data(), self._normalize_path(path))
        return value if found else default

    def try_get(self, path: str) -> tuple[bool, Any]:
        """Like :meth:`get`, but returns ``(found, value)``."""
        if not path:
            return True, self._data()
        return try_get_path_value(self._data(), self._normalize_path(path))
