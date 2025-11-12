from enum import Enum

_UNSET_FIELD = object()


class FieldAssertionType(str, Enum):
    """Defines the types of assertions that can be made on fields."""

    EQUALS = "__EQ__"
    NOT_EQUALS = "__NEQ__"
    GREATER_THAN = "__GT__"
    LESS_THAN = "__LT__"
    CONTAINS = "__IN__"
    NOT_CONTAINS = "__NIN__"
    RE_MATCH = "__RE_MATCH__"
