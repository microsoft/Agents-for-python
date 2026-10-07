"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

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
        default: Any = None,
        type_: type[Any] | None = None,
    ) -> Any | None:
        """Get a value at the dot-notation ``path``. Supports dot separators and
        bracket array indexing (e.g. ``"message.attachments[0].text"``). Returns
        ``default`` (or ``None``) when the path does not exist.

        When ``type_`` is supplied, Pydantic's ``TypeAdapter`` converts and
        validates existing values, raising ``ValidationError`` on failure.
        Existing null values are validated too; they do not use ``default``.
        Missing-path defaults are returned unchanged, without validation.
        Without ``type_``, existing values are returned as-is.
        An empty path selects the entire serialized model.
        """
        found, value = self.try_get(path)
        if not found:
            return default
        return TypeAdapter(type_).validate_python(value) if type_ is not None else value

    def try_get(self, path: str) -> tuple[bool, Any]:
        """Like :meth:`get`, but returns ``(found, value)``."""
        if not path:
            return True, self._data()
        return try_get_path_value(self._data(), self._normalize_path(path))
