from __future__ import annotations

from collections import UserDict, UserList
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any, Sequence

from ._path import (
    _get,
    _Path,
    _traverse,
    _TraverseState,
    _WildcardPath,
    _SimplePathSegment,
    _PathSegment,
    _Wildcard,
)
from ._missing import _MISSING

class _QueryList(UserList):

    def __init__(
            self,
            data: Sequence,
            base_path: _Path,
            *,
            readonly: bool = False
        ):
        super().__init__(data)
        self._readonly = readonly
        self._base_path = base_path

    def full_path(self, index: int) -> _Path:
        return self._base_path + str(index)

    def __setitem__(self, index: Any, item: Any) -> None:
        if self._readonly:
            raise RuntimeError("Cannot modify readonly _QueryList")

        self._root.update_data(self.full_path(index), item)
        super().__setitem__(index, item)

    def __delitem__(self, index: Any) -> None:
        if self._readonly:
            raise RuntimeError("Cannot modify readonly _QueryList")

        self._root.delete_shortcut(self.full_path(index))
        super().__delitem__(index)
        
@dataclass
class _ShortcutEntry:

    key: str
    value: Any

class _QueryDict(UserDict):

    def __init__(self, data: Mapping, *, base_path: _Path | None = None, readonly: bool = False):
        super().__init__()
        self._data = dict(data)
        self._base_path = base_path or _Path()
        self._readonly = readonly
        self._shortcuts: dict[str, list[_ShortcutEntry]] = {}
        self._populate_shortcuts()

    def __contains__(self, key: Any) -> bool:
        if isinstance(key, _PathSegment):
            

    def full_path(self, partial_path: int | str | _Path) -> _Path:
        return self._base_path + _Path(partial_path)

    def _normalize_value(self, value: Any, base_path: _Path) -> Any:
        if isinstance(value, (_QueryDict, _QueryList)):
            return value
        if isinstance(value, MutableMapping):
            return _QueryDict(
                value,
                base_path=base_path,
                readonly=self._readonly,
            )
        if isinstance(value, Mapping):
            return _QueryDict(value, base_path=base_path, readonly=True)
        if isinstance(value, Sequence):
            return _QueryList(value, base_path=base_path, readonly=self._readonly)
        return value

    def _populate_shortcuts(self) -> None:
        for key, val in self._data.items():
            self._data[key] = self._normalize_value(val, self.full_path(key))

    @staticmethod
    def _get_folded_key(segment: str | _PathSegment) -> str:
        return _QueryDict._ps(segment).folded

    @staticmethod
    def _ps(segment: str | _PathSegment) -> _PathSegment:
        if isinstance(segment, str):
            return _SimplePathSegment(segment)
        return segment

    def _get_shortcut(self, segment: str | _PathSegment) -> tuple[list[_ShortcutEntry] | None, _ShortcutEntry | None]:
        seg = self._ps(segment)
        entries = self._shortcuts.get(self._get_folded_key(segment), [])
        for entry in entries:
            if seg.check(entry.key):
                return entries, entry
        return entries, None

    def _get_shorcut_entry(self, segment: _PathSegment) -> _ShortcutEntry | None:
        _, entry = self._get_shortcut(segment)
        return entry if entry is not None else None

    def _update_shortcut(self, segment: str | _PathSegment, value: Any) -> None:
        entries, entry = self._get_shortcut(segment)
        if entry is not None:
            entry.value = value
        else:
            folded_key = self._get_folded_key(segment)
            if entries is None:
                entries = []
                self._shortcuts[folded_key] = entries
            entries.append(_ShortcutEntry(key=str(segment), value=value))

    def _delete_shortcut(self, segment: str | _PathSegment) -> None:
        entries, entry = self._get_shortcut(segment)
        if entry is not None and entries is not None:
            entries.remove(entry)
            if not entries:
                del self._shortcuts[self._get_folded_key(segment)]

    def __contains__(self, key: Any) -> bool:
        if isinstance(key, _Path):
            if len(key) == 0:
                return False
            if len(key) != 1:
                next_obj = self._data.get(key[0], None)
                if isinstance(next_obj, (_QueryDict, _QueryList)):
                    return key[1:] in next_obj
                return False
            key = key[0]
        if isinstance(key, _Wildcard):
            return True
        elif isinstance(key, (str, _PathSegment)):
            return self._get_shorcut_entry(self._ps(key)) is not None
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
                raise KeyError(key)

        if isinstance(key, _Wildcard):
            raise ValueError("Wildcard paths cannot be used to set a value.")

        if isinstance(key, (str, _PathSegment)):

            value = self._normalize_value(value, self.full_path(str(key)))

            shortcut, entry = self._get_shortcut(key)
            if entry is not None:
                entry.value = value
            

            
    def update_shortcut(self, key: Any) -> None:

        if not isinstance(key, (str, int)):
            raise TypeError("Key must be a string or _Path.")
        
        self._shortcuts[_SimplePathSegment(key).folded] = 

        lst = self._shortcuts.get(path.folded) or []

        if self._get_shortcut_entry(path) is None:
            lst.append(_ShortcutEntry(path=path, value=value))
            self._shortcuts[path.folded] = lst

    def delete_shortcut(self, path: _Path) -> None:

        if not path.is_simple:
            raise ValueError("Path must be simple to delete shortcut.")

        to_delete = []

        value = self.get(path, default=_MISSING)

        if isinstance(value, (Mapping, Sequence)):

            base_path_len = len(path)

            def handler(state: _TraverseState, obj: Any) -> None:
                if len(state.traversed) >= base_path_len and (
                    hash(state.traversed[:base_path_len]) == hash(path)
                ):
                    to_delete.extend(self._shortcuts.get(state.traversed.folded, []))

            _WildcardPath.traverse(value, handler)
        else:
            to_delete.append(path)

        _WildcardPath.traverse(self._data, handler)

        for path in to_delete:
            del self._data[path.last]
            entries = self._shortcuts.get(path.folded, [])
            self._shortcuts[path.folded] = [
                entry for entry in entries if hash(path) != hash(entry.path)
            ]

    def __getitem__(self, key: Any) -> Any:
       if not isinstance(key, _Path) or key.is_simple:
           return _get(self._data, key)
       else:
           # complex case