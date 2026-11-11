# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Any, Mapping

from ._path_segment import _PathSegment, _SimplePathSegment

def _get_folded_key(segment: str | _PathSegment) -> str:
    return _ps(segment).folded

def _ps(segment: str | _PathSegment) -> _PathSegment:
    if isinstance(segment, str):
        return _SimplePathSegment(segment)
    return segment

@dataclass
class _FoldedMapEntry:

    key: str
    value: Any

class _FoldedMap:

    def __init__(self, data: Mapping) -> None:
        self._data: dict[str, list[_FoldedMapEntry]] = {}
        for key, val in data.items():
            self.update_entry(key, val)

    def update_entry(self, segment: str | _PathSegment, value: Any) -> str:
        entries, entry = self._get_entry_and_bucket(segment)
        if entry is not None:
            entry.value = value
            return entry.key
        else:
            if entries is None:
                entries = []
                self._data[_get_folded_key(segment)] = entries
            segment_str = str(segment)
            entries.append(_FoldedMapEntry(key=segment_str, value=value))
            return segment_str

    def delete_entry(self, segment: str | _PathSegment) -> str | None:
        entries, entry = self._get_entry_and_bucket(segment)
        if entry is not None and entries is not None:
            key = entry.key
            entries.remove(entry)
            if not entries:
                del self._data[_get_folded_key(segment)]
            return key
        return None

    def _get_entry_and_bucket(self, segment: str | _PathSegment) -> tuple[list[_FoldedMapEntry] | None, _FoldedMapEntry | None]:
        seg = _ps(segment)
        entries = self.get_bucket(segment)
        if entries:
            for entry in entries:
                if seg.check(entry.key):
                    return entries, entry
        return entries, None

    def get_bucket(self, segment: str | _PathSegment) -> list[_FoldedMapEntry] | None:
        return self._data.get(_get_folded_key(segment), None)

    def get_entry(self, segment: _PathSegment) -> _FoldedMapEntry | None:
        _, entry = self._get_entry_and_bucket(segment)
        return entry if entry is not None else None