from typing import Any

from microsoft_agents.activity import Activity

from .type_defs import FieldAssertionType
from .check_activity import check_activity_verbose
from .check_field import check_field


def assert_activity(activity: Activity, baseline: Activity | dict) -> None:
    """Asserts that the given activity matches the baseline activity.

    :param activity: The activity to be tested.
    :param baseline: The baseline activity or a dictionary representing the expected activity data.
    """
    res, assertion_error_data = check_activity_verbose(activity, baseline)
    assert res, str(assertion_error_data)


def assert_field(
    actual_value: Any, baseline_value: Any, assertion_type: FieldAssertionType
) -> None:
    """Asserts that a specific field in the target matches the baseline.

    :param key_in_baseline: The key of the field to be tested.
    :param target: The target dictionary containing the actual values.
    :param baseline: The baseline dictionary containing the expected values.
    """
    assert check_field(actual_value, baseline_value, assertion_type)
