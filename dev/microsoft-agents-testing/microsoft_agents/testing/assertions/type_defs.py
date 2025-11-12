from enum import Enum

_UNSET_FIELD = object()


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
