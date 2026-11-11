# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator, Mapping

class _PathSegment(ABC):

    def __init__(self, string: str):
        self._string = string
        self._fold: str | None = None

    @property
    def string(self) -> str:
        return self._string

    @abstractmethod
    def isdigit(self) -> bool: ...

    @abstractmethod
    def check(self, target: Any) -> bool: ...
    
    @staticmethod
    def fold(string: str) -> str:
        return string.casefold().replace("_", "")

    @property
    def folded(self) -> str:
        if self._fold is None:
            self._fold = self.fold(self.string)
        return self._fold

    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...

    def __str__(self) -> str:
        return self.string

def _ExactPathSegment(string: str) -> _SimplePathSegment:
    return _SimplePathSegment(string, ignore_case=False, ignore_underscores=False)

class _SimplePathSegment(_PathSegment):

    def __init__(self, string: str, ignore_case: bool = False, ignore_underscores: bool = False):
        super().__init__(string)
        self._ignore_case = ignore_case
        self._ignore_underscores = ignore_underscores
        self._fold: str | None = None

    def isdigit(self) -> bool:
        return self.string.isdigit()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _SimplePathSegment):
            return self.string == other.string and self._ignore_case == other._ignore_case and self._ignore_underscores == other._ignore_underscores
        return False
    
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

        if self._ignore_case:
            target_segment = target_segment.casefold()
            segment = segment.casefold()
        if self._ignore_underscores:
            target_segment = target_segment.replace("_", "")
            segment = segment.replace("_", "")

        return segment == target_segment

    def __repr__(self) -> str:
        return f"_PathSegment(segment={self.string!r}, ignore_case={self._ignore_case}, ignore_underscores={self._ignore_underscores})"

class _Wildcard(_PathSegment):

    def __init__(self):
        super().__init__("*")

    def __eq__(self, other: Any):
        return isinstance(other, _Wildcard)

    @property
    def string(self) -> str:
        return self._string

    def isdigit(self) -> bool:
        return False

    def check(self, target: Any) -> bool:
        return True