# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Any, Mapping

from .types import _PathSegment, _SimplePathSegment, _SegmentValue


def _get_folded_key(segment: _SegmentValue | _PathSegment) -> str:
    return _ps(segment).folded


def _ps(segment: _SegmentValue | _PathSegment) -> _PathSegment:
    if isinstance(segment, (str, int)):
        return _SimplePathSegment(segment)
    return segment


@dataclass
class _FoldedMapEntry:

    key: _SegmentValue
    value: Any


class _FoldedMap:
    """Index original keys/values by casefolded, underscore-free bucket names.

    Buckets retain insertion order and distinct source spellings. Selecting a
    bucket does not establish a match: callers must apply the segment policy.
    Updates to a matched entry retain its original key.
    """

    def __init__(self, data: Mapping) -> None:
        self._data: dict[str, list[_FoldedMapEntry]] = {}
        for key, val in data.items():
            self.update_entry(key, val)

    def update_entry(self, segment: _SegmentValue | _PathSegment, value: Any) -> _SegmentValue:
        entries, entry = self._get_entry_and_bucket(segment)
        if entry is not None:
            entry.value = value
            return entry.key
        else:
            if entries is None:
                entries = []
                self._data[_get_folded_key(segment)] = entries
            key_value = _PathSegment.get_value(segment)
            entries.append(_FoldedMapEntry(key=key_value, value=value))
            return key_value

    def delete_entry(self, segment: _SegmentValue | _PathSegment) -> _SegmentValue | None:
        entries, entry = self._get_entry_and_bucket(segment)
        if entry is not None and entries is not None:
            key = entry.key
            entries.remove(entry)
            if not entries:
                del self._data[_get_folded_key(segment)]
            return key
        return None

    def _get_entry_and_bucket(
        self, segment: _SegmentValue | _PathSegment
    ) -> tuple[list[_FoldedMapEntry] | None, _FoldedMapEntry | None]:
        seg = _ps(segment)
        entries = self.get_bucket(segment)
        if entries:
            for entry in entries:
                if seg.check(entry.key):
                    return entries, entry
        return entries, None

    def get_bucket(self, segment: _SegmentValue | _PathSegment) -> list[_FoldedMapEntry] | None:
        return self._data.get(_get_folded_key(segment), None)

    def get_entry(self, segment: _PathSegment) -> _FoldedMapEntry | None:
        _, entry = self._get_entry_and_bucket(segment)
        return entry if entry is not None else None
