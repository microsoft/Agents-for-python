# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Mapping

@dataclass(frozen=True, slots=True)
class _PathSegment:

    string: str = ""
    ignore_case: bool = False
    ignore_underscores: bool = False

    def isdigit(self) -> bool:
        return self.string.isdigit()

    def check(self, target: Any) -> bool:

        if isinstance(target, int):
            if self.string.isdigit():
                return int(self.string) == target
            return False

        if not isinstance(target, (str, _PathSegment)):
            target = str(target)
        
        target_segment = target.string if isinstance(target, _PathSegment) else target
        segment = self.string

        if self.string.isdigit() and target_segment.isdigit():
            return int(self.string) == int(target_segment)

        if self.ignore_case:
            target_segment = target_segment.casefold()
            segment = segment.casefold()
        if self.ignore_underscores:
            target_segment = target_segment.replace("_", "")
            segment = segment.replace("_", "")

        return segment == target_segment

    def contained_by(self, obj: Any) -> bool:
        if isinstance(obj, Mapping):
            return any(self.check(key) for key in obj)
        if isinstance(obj, list) and self.string.isdigit():
            index = int(self.string)
            return 0 <= index < len(obj)
        return False

    def step_once(self, obj: Any) -> tuple[bool, Any, Any]:
        try:
            key, next_obj = next(self.iter_steps(obj))
            return True, key, next_obj
        except StopIteration:
            return False, None, None

    def iter_steps(self, obj: Any) -> Iterator[tuple[Any, Any]]:
        if isinstance(obj, Mapping):
            for key in obj:
                if self.check(key):
                    yield key, obj[key]
        elif isinstance(obj, list) and self.string.isdigit():
            index = int(self.string)
            if 0 <= index < len(obj):
                yield index, obj[index]

    def __repr__(self) -> str:
        return f"_PathSegment(segment={self.string!r}, ignore_case={self.ignore_case}, ignore_underscores={self.ignore_underscores})"

class _Wildcard(_PathSegment):

    def __init__(self):
        super().__init__(string="*", ignore_case=True, ignore_underscores=True)

    def check(self, target: Any) -> bool:
        return True