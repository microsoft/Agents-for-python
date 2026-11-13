# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

_SegmentValue = str | int


class _PathSegment(ABC):

    def __init__(self, value: _SegmentValue):
        if not isinstance(value, (str, int)):
            raise TypeError("Path segment must be a string or integer")
        if isinstance(value, str) and (value == "" or "::" in value):
            raise ValueError(
                "Path segments must not be empty and must not contain '::'"
            )
        self._value = value
        self._string = str(value)
        self._fold: str | None = None

    @staticmethod
    def get_value(segment: _SegmentValue | _PathSegment) -> _SegmentValue:
        return segment.value if isinstance(segment, _PathSegment) else segment

    @property
    def value(self) -> _SegmentValue:
        return self._value

    @staticmethod
    def is_int_value(value: _SegmentValue) -> bool:
        return isinstance(value, int) or (
            isinstance(value, str)
            and value.isascii()
            and value.isdecimal()
            and (len(value) == 1 or value[0] != "0")
        )

    def has_int_value(self) -> bool:
        return self.is_int_value(self.value)

    @property
    def string(self) -> str:
        return self._string

    @abstractmethod
    def isdecimal(self) -> bool: ...

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
        self,
        value: _SegmentValue,
        ignore_case: bool = False,
        ignore_underscores: bool = False,
    ):
        super().__init__(value)
        self._ignore_case = ignore_case
        self._ignore_underscores = ignore_underscores
        self._fold: str | None = None
        self._transformed_string: str = self._transform(self.string)

    def isdecimal(self) -> bool:
        return self.string.isdecimal()

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
            if self.has_int_value():
                return int(self.value) == target
            return False

        if not isinstance(target, (str, _PathSegment)):
            target = str(target)

        target_segment = target.value if isinstance(target, _PathSegment) else target

        if self.has_int_value() and _PathSegment.is_int_value(target_segment):
            return int(self.value) == int(target_segment)

        return self._transformed_string == self._transform(str(target_segment))

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

    def isdecimal(self) -> bool:
        return False

    def check(self, target: Any) -> bool:
        return True
