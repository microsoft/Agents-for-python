import re
from typing import Any

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
