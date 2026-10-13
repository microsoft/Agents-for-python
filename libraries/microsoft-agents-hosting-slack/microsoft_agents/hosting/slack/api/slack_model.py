"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from types import NoneType
from typing import Any, TypeVar, overload

from pydantic import BaseModel, ConfigDict, TypeAdapter

from .._path_navigator import try_get_path_value

_T = TypeVar("_T")
_DefaultT = TypeVar("_DefaultT")


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

    @overload
    def get(self, path: str, default: _DefaultT, type_: type[_T]) -> _T | _DefaultT: ...

    @overload
    def get(self, path: str, *, type_: type[_T]) -> _T | None: ...

    @overload
    def get(self, path: str, default: Any = None, type_: None = None) -> Any: ...

    def get(
        self,
        path: str,
        default: _DefaultT | None = None,
        type_: type[_T] | None = None,
    ) -> _T | _DefaultT | None:
        """Get a value at the dot-notation ``path``. Supports dot separators and
        bracket array indexing (e.g. ``"message.attachments[0].text"``). Returns
        ``default`` (or ``None``) when the path does not exist.

        When ``type_`` is supplied, Pydantic's ``TypeAdapter`` converts and
        validates non-null values, raising ``ValidationError`` on failure.
        Existing null values return ``default`` (or ``None``) for typed lookups,
        except when ``type_`` is ``type(None)``, which validates null directly.
        Defaults are returned unchanged, without validation.
        Without ``type_``, existing values are returned as-is, including null.
        An empty path selects the entire serialized model.

        For example, ``response.get("count", type_=int)`` converts a value to
        an integer, while ``envelope.get("event", type_=EventContent)``
        validates it as an event model. Invalid non-null values raise
        ``pydantic.ValidationError`` even when a default is provided.

        Typed overloads return the requested type plus ``None`` when no
        default is supplied, or the requested type plus the default's type
        when one is supplied. Untyped lookups remain dynamically typed.
        """
        found, value = self.try_get(path)
        if not found:
            return default
        if type_ is not None and type_ is not NoneType and value is None:
            return default
        return TypeAdapter(type_).validate_python(value) if type_ is not None else value

    def try_get(self, path: str) -> tuple[bool, Any]:
        """Return a raw ``(found, value)`` tuple without conversion or validation.

        An existing null value returns ``(True, None)``; a missing path returns
        ``(False, None)``. An empty path selects the entire serialized model.
        """
        if not path:
            return True, self._data()
        return try_get_path_value(self._data(), self._normalize_path(path))
