from enum import Enum

_UNSET_FIELD = object()


class FieldAssertionType(Enum):
    """Defines the types of assertions that can be made on fields."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    RE_MATCH = "re_match"
