# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from collections import UserDict
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any, Sequence
from typing_extensions import Self

from ._folded_map import _FoldedMap, _ps
from ._path import _Path
from ._path_segment import _PathSegment, _Wildcard
from ._user_dict import _UserDict
from ._user_list import _UserList
from ._utils import (
    _set,
    _pop,
)

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

    def __init__(
            self,
            data,
            # base_path: _Path,
            /,
        ):
        self._data = [ _normalize_value(value) for index, value in enumerate(data) ]

    # def full_path(self, index: int) -> _Path:
    #     return self._base_path + str(index)

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

    def get_with_key(self, index: Any) -> tuple[Any, _Path]:
        if isinstance(index, _Path):
            if not index.is_simple:
                raise ValueError("Path must be simple to set a value.")

            if not index:
                raise ValueError("Path must not be empty.")

            if len(index) == 1:
                index = index[0]
            else:
                i = index[0]
                if i.isdigit() and 0 <= int(i.string) < len(self):
                    next_obj = self._data[int(i.string)]

                    if not isinstance(next_obj, (_QueryList, _QueryDict)):
                        raise TypeError("Path of length > 1 must refer to a mapping.")

                    value, path = next_obj.get_with_key(index[1:])
                    return value, _Path.exact(i.string) + path
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
            value = super().__getitem__(index)
            return value, _Path.exact(str(index))
        
        raise TypeError("List index must be an integer or a digit string.")

    def __contains__(self, item) -> bool:
        return self.get_with_key(item)[0] is not None

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, slice):
            return super().__getitem__(index)
        return self.get_with_key(index)[0]

    def __setitem__(self, index: Any, item: Any) -> None:

        if isinstance(index, _Path):
            if not index.is_simple:
                raise ValueError("Path must be simple to set a value.")

            if not index:
                raise ValueError("Path must not be empty.")

            if len(index) == 1:
                index = index[0]
            else:
                i = index[0]
                if i.isdigit() and 0 <= int(i.string) < len(self):
                    next_obj = self._data[int(i.string)]
                    if not isinstance(next_obj, (_QueryDict, _QueryList)):
                        raise TypeError("Cannot set a nested value on a non-dictionary or non-list.")
                    next_obj[index[1:]] = _normalize_value(item)
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
            super().__setitem__(index, _normalize_value(item))
            return
        raise TypeError("List index must be an integer or a digit string.")

    def __delitem__(self, index: Any) -> None:

        if isinstance(index, _Path):
            if not index.is_simple:
                raise ValueError("Path must be simple to delete a value.")

            if not index:
                raise ValueError("Path must not be empty.")

            if len(index) == 1:
                index = index[0]
            else:
                i = index[0]
                if i.isdigit() and 0 <= int(i.string) < len(self):
                    _pop(self._data[int(i.string)], index[1:])
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
            return
        raise TypeError("List index must be an integer or a digit string.")

        

class _QueryDict(_UserDict):

    def __init__(self, data: Mapping | None = None, /, **kwargs):

        data = data or {}

        data = dict(data)
        for key, val in data.items():
            data[key] = _normalize_value(val)
        self._shortcuts = _FoldedMap(data)

        super().__init__(data, False, **kwargs)

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["_data"] = self.__dict__["_data"].copy()
        inst.__dict__["_shortcuts"] = _FoldedMap(inst.__dict__["_data"])
        return inst

    # def full_path(self, partial_path: int | str | _Path) -> _Path:
    #     if isinstance(partial_path, _Path):
    #         return self._base_path + partial_path
    #     return self._base_path + _Path(str(partial_path))

    def __contains__(self, key: Any) -> bool:
        if isinstance(key, _Path):
            if len(key) == 0:
                return False
            if len(key) != 1:
                entry = self._shortcuts.get_entry(_ps(key[0]))
                next_obj = entry.value if entry is not None else None
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
                entry = self._shortcuts.get_entry(_ps(key[0]))
                next_obj = entry.value if entry is not None else None
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    next_obj[key[1:]] = value
                    return
                raise TypeError("Path must refer to a nested _QueryDict or _QueryList.")

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to set a value.")

        if isinstance(key, (str, _PathSegment)):
            value = _normalize_value(value)
            actual_key = self._shortcuts.update_entry(_ps(key), value)
            super().__setitem__(actual_key, value)
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
                entry = self._shortcuts.get_entry(_ps(key[0]))
                next_obj = entry.value if entry is not None else None
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    del next_obj[key[1:]]
                    return
                raise TypeError("Path must refer to a nested _QueryDict or _QueryList.")

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to delete a value.")

        if isinstance(key, (str, _PathSegment)):
            actual_key = self._shortcuts.delete_entry(_ps(key))
            if actual_key is None:
                raise KeyError(key)
            super().__delitem__(actual_key)
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def get_with_key(self, key: Any) -> tuple[Any, _Path]:

        if isinstance(key, _Path):
            if not key.is_simple:
                raise ValueError("Path must be simple to get a value.")

            if len(key) == 0:
                raise ValueError("Path must not be empty.")

            if len(key) == 1:
                key = key[0]
            else:
                entry = self._shortcuts.get_entry(_ps(key[0]))
                next_obj = entry.value if entry is not None else None
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    assert entry is not None
                    val, path = next_obj.get_with_key(key[1:])
                    return val, _Path.exact(entry.key) + path
                raise TypeError("Path must refer to a nested _QueryDict or _QueryList.")

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to get a value.")

        if isinstance(key, (str, _PathSegment)):
            entry = self._shortcuts.get_entry(_ps(key))
            if entry is not None:
                return entry.value, _Path.exact(entry.key)
            raise KeyError(key)
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def __getitem__(self, key: Any) -> Any:
        return self.get_with_key(key)[0]

    def __ior__(self, other: Any) -> Self:
        if not isinstance(other, _QueryDict) and isinstance(other, UserDict):
            other = other.data
        self.update(other)
        return self