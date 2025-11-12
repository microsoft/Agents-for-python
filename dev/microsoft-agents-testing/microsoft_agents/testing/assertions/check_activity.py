from typing import Any, TypeVar, Optional

from pydantic import BaseModel

from microsoft_agents.activity import Activity
from microsoft_agents.testing.utils import normalize_activity_data

from .check_field import check_field
from .type_defs import UNSET_FIELD, FieldAssertionType


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
        assertion_type = field["assertion_type"]
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

def _check(actual: Any, baseline: Any) -> bool:

    assertion, assertion_type = _parse_assertion(baseline)

    if assertion_type is None:
        if isinstance(baseline, dict):
            for key in baseline:
                new_actual = actual.get(key, UNSET_FIELD)
                new_baseline = baseline[key]
                if not _check(new_actual, new_baseline):
                    return False
                
        elif isinstance(baseline, list):
            for index, item in enumerate(baseline):
                new_actual = actual[index] if index < len(actual) else UNSET_FIELD
                new_baseline = item
                if not _check(new_actual, new_baseline):
                    return False
        else:
            raise ValueError("Unsupported baseline type for complex assertion.")
    else:
        assert assertion_type
        assertion, assertion_type = _parse_assertion(baseline)
        if not check_field(actual, assertion, assertion_type):
            return False


def check_activity(activity: Activity, baseline: Activity | dict) -> bool:
    """Asserts that the given activity matches the baseline activity.

    :param activity: The activity to be tested.
    :param baseline: The baseline activity or a dictionary representing the expected activity data.
    """
    actual_activity = normalize_activity_data(activity)
    baseline = normalize_activity_data(baseline)
    return _check(actual_activity, baseline)