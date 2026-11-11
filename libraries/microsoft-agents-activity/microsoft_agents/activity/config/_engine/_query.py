# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections import UserDict
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, Sequence
from typing_extensions import Self

from ._folded_map import _FoldedMap, _ps
from ._path import (
    _get,
    _set,
    _pop,
    _Path,
    _traverse,
    _TraverseState,
    _WildcardPath,
    _SimplePathSegment,
    _PathSegment,
    _Wildcard,
)
from ._user_dict import _UserDict
from ._user_list import _UserList
from ._missing import _MISSING

class _QueryList(_UserList):

    def __init__(
            self,
            data,
            base_path: _Path,
            /,
        ):
        super().__init__(data)
        self._base_path = base_path

    def full_path(self, index: int) -> _Path:
        return self._base_path + str(index)

    def __setitem__(self, index: Any, item: Any) -> None:

        if isinstance(index, _Path):
            if not index.is_simple:
                raise ValueError("Path must be simple to set a value.")

            if not index:
                raise ValueError("Path must not be empty.")

            if len(index) == 1:
                index = index[0]
            else:
                index = index[0]
                if index.isdigit() and 0 <= int(index.string) < len(self):
                    _set(self._data[int(index.string)], index[1:], item)
                    return
                raise IndexError("List index out of range.")

        if isinstance(index, _PathSegment):
            if not index.isdigit():
                raise TypeError("List index must be an integer or a digit string.")
            if isinstance(index, _Wildcard):
                raise TypeError("List index must be an integer or a digit string.")

        if isinstance(index, (int, _PathSegment)):
            index = int(index.string) if isinstance(index, _PathSegment) else index

            if index < 0 or index >= len(self):
                raise IndexError("List index out of range.")
            super().__setitem__(index, item)

    def __delitem__(self, index: Any) -> None:

        if isinstance(index, _Path):
            if not index.is_simple:
                raise ValueError("Path must be simple to delete a value.")

            if not index:
                raise ValueError("Path must not be empty.")

            if len(index) == 1:
                index = index[0]
            else:
                index = index[0]
                if index.isdigit() and 0 <= int(index.string) < len(self):
                    _pop(self._data[int(index.string)], index[1:])
                    return
                raise IndexError("List index out of range.")

        if isinstance(index, _PathSegment):
            if not index.isdigit():
                raise TypeError("List index must be an integer or a digit string.")
            if isinstance(index, _Wildcard):
                raise TypeError("List index must be an integer or a digit string.")

        if isinstance(index, (int, _PathSegment)):
            index = int(index.string) if isinstance(index, _PathSegment) else index

            if index < 0 or index >= len(self):
                raise IndexError("List index out of range.")
            super().__delitem__(index)

        

class _QueryDict(_UserDict):

    def __init__(self, data: Mapping, _base_path: _Path | None = None, /, **kwargs):

        self._base_path = _base_path or _Path()

        data = dict(data)
        for key, val in data.items():
            data[key] = self._normalize_value(val, self.full_path(key))
        self._shortcuts = _FoldedMap(data)

        super().__init__(data, False, **kwargs)

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["_data"] = self.__dict__["_data"].copy()
        inst.__dict__["_shortcuts"] = _FoldedMap(inst.__dict__["_data"])
        return inst

    def full_path(self, partial_path: int | str | _Path) -> _Path:
        if isinstance(partial_path, _Path):
            return self._base_path + partial_path
        return self._base_path + _Path(str(partial_path))

    def _normalize_value(self, value: Any, base_path: _Path) -> Any:
        if isinstance(value, (_QueryDict, _QueryList)):
            return value
        if isinstance(value, MutableMapping):
            return _QueryDict(value, base_path)
        if isinstance(value, Mapping):
            return _QueryDict(value, base_path)
        if isinstance(value, Sequence) and not isinstance(value, str):
            return _QueryList(value, base_path)
        return value

    def __contains__(self, key: Any) -> bool:
        if isinstance(key, _Path):
            if len(key) == 0:
                return False
            if len(key) != 1:
                next_obj = self._data.get(key[0], None)
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    return key[1:] in next_obj
                raise TypeError("Path must refer to a nested _QueryDict or _QueryList.")
            key = key[0]
        if isinstance(key, _Wildcard):
            return True
        elif isinstance(key, (str, _PathSegment)):
            return self._shortcuts.get_entry(_ps(key)) is not None
        return super().__contains__(key)

    def __setitem__(self, key: Any, value: Any) -> None:

        if isinstance(key, _Path):
            if not key.is_simple:
                raise ValueError("Path must be simple to set a value.")

            if len(key) == 0:
                raise ValueError("Path must not be empty.")

            if len(key) == 1:
                key = key[0]
            else:
                next_obj = self._data.get(key[0], None)
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    next_obj[key[1:]] = value
                    return
                raise TypeError("Path must refer to a nested _QueryDict or _QueryList.")

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to set a value.")

        if isinstance(key, (str, _PathSegment)):
            value = self._normalize_value(value, self.full_path(str(key)))
            super().__setitem__(key, value) # ensure update occurs before shortcuts are modified
            self._shortcuts.update_entry(_ps(key), value)
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def __delitem__(self, key: Any) -> None:
        if isinstance(key, _Path):
            if not key.is_simple:
                raise ValueError("Path must be simple to delete a value.")

            if len(key) == 0:
                raise ValueError("Path must not be empty.")

            if len(key) == 1:
                key = key[0]
            else:
                next_obj = self._data.get(key[0], None)
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    del next_obj[key[1:]]
                    return
                raise TypeError("Path must refer to a nested _QueryDict or _QueryList.")

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to delete a value.")

        if isinstance(key, (str, _PathSegment)):
            super().__delitem__(key)
            self._shortcuts.delete_entry(_ps(key))
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def __getitem__(self, key: Any) -> Any:

        if isinstance(key, _Path):
            if not key.is_simple:
                raise ValueError("Path must be simple to get a value.")

            if len(key) == 0:
                raise ValueError("Path must not be empty.")

            if len(key) == 1:
                key = key[0]
            else:
                next_obj = self._data.get(key[0], None)
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    return next_obj[key[1:]]
                raise TypeError("Path must refer to a nested _QueryDict or _QueryList.")

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to get a value.")

        if isinstance(key, (str, _PathSegment)):
            super().__getitem__(key)
            entry = self._shortcuts.get_entry(_ps(key))
            if entry is not None:
                return entry.value
            return None
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def __ior__(self, other: Any) -> Self:
        if not isinstance(other, _QueryDict) and isinstance(other, UserDict):
            other = other.data
        self.update(other)
        return self