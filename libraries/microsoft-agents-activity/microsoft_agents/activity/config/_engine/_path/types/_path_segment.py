# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
    """Match one key with explicit case and underscore policies.

    The broader folded form is only an index bucket key; ``check`` applies the
    requested policy. Decimal segments compare by numeric value, including
    comparisons with integer mapping keys.
    """

    def __init__(
        self, string: str | int, ignore_case: bool = False, ignore_underscores: bool = False
    ):
        if isinstance(string, str) and not string:
            raise ValueError("Path segment cannot be empty")
        
        super().__init__(str(string))
        self._ignore_case = ignore_case
        self._ignore_underscores = ignore_underscores
        self._fold: str | None = None
        self._transformed_string: str = self._transform(self.string)

    def isdigit(self) -> bool:
        return self.string.isdigit()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _SimplePathSegment):
            return (
                self.string == other.string
                and self._ignore_case == other._ignore_case
                and self._ignore_underscores == other._ignore_underscores
            )
        return False

    def _transform(self, string: str) -> str:
        
        if self._ignore_case:
            string = string.casefold()
        if self._ignore_underscores:
            string = string.replace("_", "")
        return string

    def check(self, target: Any) -> bool:

        if isinstance(target, int):
            if self.string.isdigit():
                return int(self.string) == target
            return False

        if not isinstance(target, (str, _PathSegment)):
            target = str(target)

        target_segment = target.string if isinstance(target, _PathSegment) else target

        if self.string.isdigit() and target_segment.isdigit():
            return int(self.string) == int(target_segment)

        return self._transformed_string == self._transform(target_segment)

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
