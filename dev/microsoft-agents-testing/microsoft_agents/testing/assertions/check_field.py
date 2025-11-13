import re
from typing import Any, Optional

from .type_defs import FieldAssertionType, UNSET_FIELD

_OPERATIONS = {
    FieldAssertionType.EQUALS: lambda a, b: a == b or (a is UNSET_FIELD and b is None),
    FieldAssertionType.NOT_EQUALS: lambda a, b: a != b or (a is UNSET_FIELD and b is not None),
    FieldAssertionType.GREATER_THAN: lambda a, b: a > b,
    FieldAssertionType.LESS_THAN: lambda a, b: a < b,
    FieldAssertionType.CONTAINS: lambda a, b: b in a,
    FieldAssertionType.NOT_CONTAINS: lambda a, b: b not in a,
    FieldAssertionType.RE_MATCH: lambda a, b: re.match(b, a) is not None,
}

def _parse_assertion(field: Any) -> tuple[Any, Optional[FieldAssertionType]]:
    """Parses the assertion information and returns the assertion type and baseline value.

    :param assertion_info: The assertion information to be parsed.
    :return: A tuple containing the assertion type and baseline value.
    """

    assertion_type = FieldAssertionType.EQUALS
    assertion = None

    if (
        isinstance(field, dict)
        and "assertion_type" in field
        and "assertion" in field
        and field["assertion_type"] in FieldAssertionType.__members__
    ):
        # format:
        # {"assertion_type": "__EQ__", "assertion": "value"}
        assertion_type = FieldAssertionType[field["assertion_type"]]
        assertion = field.get("assertion")

    elif (
        isinstance(field, list)
        and len(field) >= 2
        and isinstance(field[0], str)
        and field[0] in FieldAssertionType.__members__
    ):
        # format:
        # ["__EQ__", "assertion"]
        assertion_type = FieldAssertionType[field[0]]
        assertion = field[1]
    elif isinstance(field, list) or isinstance(field, dict):
        assertion_type = None
    else:
        # default format: direct value
        assertion = field

    return assertion, assertion_type

def check_field(
    actual_value: Any, assertion: Any, assertion_type: FieldAssertionType
) -> bool:
    """Checks if the actual value satisfies the given assertion based on the assertion type.
    
    :param actual_value: The value to be checked.
    :param assertion: The expected value or pattern to check against.
    :param assertion_type: The type of assertion to perform.
    :return: True if the assertion is satisfied, False otherwise.
    """

    operation = _OPERATIONS.get(assertion_type)
    if not operation:
        return False  # missing operation for the assertion type
    return operation(actual_value, assertion)
