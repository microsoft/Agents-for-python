# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections import UserDict
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any, Sequence
from typing_extensions import Self

from ._folded_map import _FoldedMap, _ps
from .types import (
    _Path,
    _PathSegment,
    _Wildcard,
    _UserDict,
    _UserList,
    _MISSING,
)
from ._traverse import _LookupResult, _lookup


def _normalize_value(value: Any) -> Any:
    if isinstance(value, (_QueryDict, _QueryList)):
        return value
    if isinstance(value, MutableMapping):
        return _QueryDict(value)
    if isinstance(value, Mapping):
        return _QueryDict(value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return _QueryList(value)
    return value


class _QueryList(_UserList):
    """List wrapper that normalizes inserted mappings and sequences.

    Integer and slice reads retain list semantics, including negative indexes.
    Internal paths traverse nonnegative numeric positions. Membership uses
    ordinary value equality. Slice replacements are normalized before the
    backing list is changed, and extended slices retain Python's length rules.
    """

    def __init__(
        self,
        data,
        /,
    ):
        self._data = [_normalize_value(value) for index, value in enumerate(data)]

    def copy(self) -> _QueryList:
        return self.__class__(self)

    def append(self, item: Any) -> None:
        super().append(_normalize_value(item))

    def insert(self, index: int, item: Any) -> None:
        super().insert(index, _normalize_value(item))

    def extend(self, other: Iterable[Any]) -> None:
        if other is self:
            other = self._data.copy()
        super().extend(_normalize_value(item) for item in other)

    def __iadd__(self, other: Iterable[Any]) -> Self:
        self.extend(other)
        return self

    def _lookup(self, index: Any, include_path: bool = False) -> _LookupResult:
        if isinstance(index, _Path):
            if len(index) == 1:
                index = index[0]
            else:
                result = _lookup(self, index, include_path=include_path)
                if not result.found:
                    raise KeyError(index.last)
                return result

        if isinstance(index, _PathSegment):
            if not index.isdigit():
                raise TypeError("List index must be an integer or a digit string.")
            if isinstance(index, _Wildcard):
                raise TypeError("List index must be an integer or a digit string.")

        if isinstance(index, (int, _PathSegment)):
            index = int(index.string) if isinstance(index, _PathSegment) else index

            if index < -len(self) or index >= len(self):
                raise IndexError("List index out of range.")
            value = super().__getitem__(index)
            return _LookupResult(
                found=True,
                value=value,
                matched_keys=[index] if include_path else [],
            )

        raise TypeError("List index must be an integer or a digit string.")

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, (slice, int)):
            return super().__getitem__(index)
        return self._lookup(index).value

    def __setitem__(self, index: Any, item: Any) -> None:
        from ._utils import _set

        if isinstance(index, slice):
            super().__setitem__(index, [_normalize_value(value) for value in item])
            return

        if isinstance(index, _Path):

            if len(index) == 1:
                index = index[0]
            else:
                _set(self, index, _normalize_value(item))
                return

        if isinstance(index, _PathSegment):
            if not index.isdigit():
                raise TypeError("List index must be an integer or a digit string.")
            if isinstance(index, _Wildcard):
                raise TypeError("List index must be an integer or a digit string.")

        if isinstance(index, (int, _PathSegment)):
            index = int(index.string) if isinstance(index, _PathSegment) else index

            if index >= len(self) or -len(self) > index:
                raise IndexError("List index out of range.")
            super().__setitem__(index, _normalize_value(item))
            return
        raise TypeError("List index must be an integer or a digit string.")

    def __delitem__(self, index: Any) -> None:
        from ._utils import _pop

        if isinstance(index, slice):
            super().__delitem__(index)
            return

        if isinstance(index, _Path):

            val = _pop(self, index, default=_MISSING)
            if val is _MISSING:
                raise KeyError(str(index))
            return

        if isinstance(index, _PathSegment):
            if not index.isdigit():
                raise TypeError("List index must be an integer or a digit string.")
            if isinstance(index, _Wildcard):
                raise TypeError("List index must be an integer or a digit string.")

        if isinstance(index, (int, _PathSegment)):
            index = int(index.string) if isinstance(index, _PathSegment) else index

            if index < -len(self) or index >= len(self):
                raise IndexError("List index out of range.")
            super().__delitem__(index)
            return
        raise TypeError("List index must be an integer or a digit string.")


class _QueryDict(_UserDict):
    """Mapping wrapper with literal keys and indexed internal path matching.

    Mapping updates synchronize the folded index and normalize nested values.
    Copies own a new outer mapping/index but may share nested query wrappers.
    Multi-segment path membership tests existence, including ``None`` leaves.
    """

    def __init__(self, data: Mapping | None = None, /, **kwargs):
        self._shortcuts = _FoldedMap({})
        super().__init__(data, **kwargs)

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["_data"] = self.__dict__["_data"].copy()
        inst.__dict__["_shortcuts"] = _FoldedMap(inst.__dict__["_data"])
        return inst

    def __contains__(self, key: Any) -> bool:
        if isinstance(key, _Path):
            if len(key) == 0:
                return False
            if len(key) != 1:
                return _lookup(self, key).found
            key = key[0]
        if isinstance(key, _Wildcard):
            return True
        elif isinstance(key, (str, int, _PathSegment)):
            return self._shortcuts.get_entry(_ps(key)) is not None
        return super().__contains__(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        from ._utils import _set

        if isinstance(key, _Path):
            if len(key) == 1:
                key = key[0]
            else:
                _set(self, key, value)
                return

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to set a value.")

        if isinstance(key, (str, int, _PathSegment)):
            value = _normalize_value(value)
            actual_key = self._shortcuts.update_entry(_ps(key), value)
            super().__setitem__(actual_key, value)
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def __delitem__(self, key: Any) -> None:
        from ._utils import _pop

        if isinstance(key, _Path):
            if len(key) == 1:
                key = key[0]
            else:
                val = _pop(self, key, default=_MISSING)
                if val is _MISSING:
                    raise KeyError(str(key))
                return

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to delete a value.")

        if isinstance(key, (str, int, _PathSegment)):
            actual_key = self._shortcuts.delete_entry(_ps(key))
            if actual_key is None:
                raise KeyError(str(key))
            super().__delitem__(actual_key)
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def _lookup(self, key: Any, include_path: bool = False) -> _LookupResult:

        if isinstance(key, _Path):
            if not key.is_simple:
                raise ValueError("Path must be simple to get a value.")

            if len(key) == 0:
                raise ValueError("Path must not be empty.")

            if len(key) == 1:
                key = key[0]
            else:
                result = _lookup(self, key, include_path=include_path)
                return result

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to get a value.")

        if isinstance(key, (str, int, _PathSegment)):
            entry = self._shortcuts.get_entry(_ps(key))
            if entry is not None:
                return _LookupResult(
                    found=True,
                    value=entry.value,
                    matched_keys=[entry.key] if include_path else None,
                )
            else:
                return _LookupResult(found=False)
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def __getitem__(self, key: Any) -> Any:
        result = self._lookup(key)
        if not result.found:
            raise KeyError(_PathSegment.get_value(key))
        return result.value

    def __ior__(self, other: Any) -> Self:
        if not isinstance(other, _QueryDict) and isinstance(other, UserDict):
            other = other.data
        self.update(other)
        return self
