import re
from typing import Any

from .type_defs import FieldAssertionType

_OPERATIONS = {
    FieldAssertionType.EQUALS: lambda a, b: a == b,
    FieldAssertionType.NOT_EQUALS: lambda a, b: a != b,
    FieldAssertionType.GREATER_THAN: lambda a, b: a > b,
    FieldAssertionType.LESS_THAN: lambda a, b: a < b,
    FieldAssertionType.CONTAINS: lambda a, b: b in a,
    FieldAssertionType.NOT_CONTAINS: lambda a, b: b not in a,
    FieldAssertionType.RE_MATCH: lambda a, b: re.match(b, a) is not None,
}


def check_field(
    actual_value: Any, baseline_value: Any, assertion_type: FieldAssertionType
) -> bool:
    
    operation = _OPERATIONS.get(assertion_type)
    if not operation:
        return False  # missing operation for the assertion type
    return operation(actual_value, baseline_value)
