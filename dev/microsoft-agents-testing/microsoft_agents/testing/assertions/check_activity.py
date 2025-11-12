from typing import Any

from microsoft_agents.activity import Activity
from microsoft_agents.testing.utils import normalize_activity_data

from .check_field import check_field
from .type_defs import _UNSET_FIELD, FieldAssertionType


def _parse_assertion(assertion_info: Any) -> tuple[Any, FieldAssertionType]:
    """Parses the assertion information and returns the assertion type and baseline value.

    :param assertion_info: The assertion information to be parsed.
    :return: A tuple containing the assertion type and baseline value.
    """

    assertion_type = FieldAssertionType.EQUALS

    if isinstance(assertion_info, dict) and "assertion_type" in assertion_info:
        # format:
        # {"assertion_type": "__EQ__", "assertion": "value"}
        assertion_type = assertion_info["assertion_type"]
        assertion = assertion_info.get("assertion")

    elif isinstance(assertion_info, list) and \
            len(assertion_info) >= 1 and \
            isinstance(assertion_info[0], str) and \
            assertion_info[0] in FieldAssertionType.__members__:
        # format:
        # ["__EQ__", "assertion"]
        assertion_type = FieldAssertionType[assertion_info[0]]
        assertion = assertion_info[1] if len(assertion_info) > 1 else None
    else:
        # default format: direct value
        assertion = assertion_info

    return assertion, assertion_type

def check_activity(activity: Activity, baseline: Activity | dict) -> bool:
    """Asserts that the given activity matches the baseline activity.

    :param activity: The activity to be tested.
    :param baseline: The baseline activity or a dictionary representing the expected activity data.
    """

    baseline = normalize_activity_data(baseline)

    for key in baseline.keys():
        # support for different assertion formats
        assertion, assertion_type = _parse_assertion(baseline[key])
        target_value = getattr(activity, key, _UNSET_FIELD)

        if not check_field(target_value, assertion, assertion_type):
            return False
        
    return True
