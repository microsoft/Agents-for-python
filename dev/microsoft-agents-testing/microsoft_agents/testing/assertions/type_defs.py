# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any


class UNSET_FIELD:
    """Singleton to represent an unset field in activity comparisons."""

    @staticmethod
    def get(*args, **kwargs):
        """Returns the singleton instance."""
        return UNSET_FIELD


class FieldAssertionType(str, Enum):
    """Defines the types of assertions that can be made on fields."""

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    RE_MATCH = "RE_MATCH"


class AssertionQuantifier(str, Enum):
    """Defines quantifiers for assertions on activities."""

    ANY = "ANY"
    ALL = "ALL"
    ONE = "ONE"
    NONE = "NONE"

    @staticmethod
    def from_config(value: str) -> AssertionQuantifier:
        """Creates an AssertionQuantifier from a configuration string.

        :param value: The configuration string.
        :return: The corresponding AssertionQuantifier.
        """
        value = value.upper()
        if value not in AssertionQuantifier:
            raise ValueError(f"Invalid AssertionQuantifier value: {value}")
        return AssertionQuantifier(value)


@dataclass
class AssertionErrorData:
    """Data class to hold information about assertion errors."""

    field_path: str
    actual_value: Any
    assertion: Any
    assertion_type: FieldAssertionType

    def __str__(self) -> str:
        return (
            f"Assertion failed at '{self.field_path}': "
            f"actual value '{self.actual_value}' "
            f"does not satisfy assertion '{self.assertion}' "
            f"of type '{self.assertion_type}'."
        )
