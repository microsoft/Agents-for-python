# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Optional

from microsoft_agents.activity import Activity
from microsoft_agents.testing.utils import normalize_activity_data

from .check_field import check_field, _parse_assertion
from .type_defs import UNSET_FIELD, FieldAssertionType, AssertionErrorData


def _check(
    actual: Any, baseline: Any, field_path: str = ""
) -> tuple[bool, Optional[AssertionErrorData]]:
    """Recursively checks the actual data against the baseline data.

    :param actual: The actual data to be tested.
    :param baseline: The baseline data to compare against.
    :param field_path: The current field path being checked (for error reporting).
    :return: A tuple containing a boolean indicating success and optional assertion error data.
    """

    assertion, assertion_type = _parse_assertion(baseline)

    if assertion_type is None:
        if isinstance(baseline, dict):
            for key in baseline:
                new_field_path = f"{field_path}.{key}" if field_path else key
                new_actual = actual.get(key, UNSET_FIELD)
                new_baseline = baseline[key]

                res, assertion_error_data = _check(
                    new_actual, new_baseline, new_field_path
                )
                if not res:
                    return False, assertion_error_data
            return True, None

        elif isinstance(baseline, list):
            for index, item in enumerate(baseline):
                new_field_path = (
                    f"{field_path}[{index}]" if field_path else f"[{index}]"
                )
                new_actual = actual[index] if index < len(actual) else UNSET_FIELD
                new_baseline = item

                res, assertion_error_data = _check(
                    new_actual, new_baseline, new_field_path
                )
                if not res:
                    return False, assertion_error_data
            return True, None
        else:
            raise ValueError("Unsupported baseline type for complex assertion.")
    else:
        assert isinstance(assertion_type, FieldAssertionType)
        res = check_field(actual, assertion, assertion_type)
        if res:
            return True, None
        else:
            assertion_error_data = AssertionErrorData(
                field_path=field_path,
                actual_value=actual,
                assertion=assertion,
                assertion_type=assertion_type,
            )
            return False, assertion_error_data


def check_activity(activity: Activity, baseline: Activity | dict) -> bool:
    """Asserts that the given activity matches the baseline activity.

    :param activity: The activity to be tested.
    :param baseline: The baseline activity or a dictionary representing the expected activity data.
    """
    return check_activity_verbose(activity, baseline)[0]


def check_activity_verbose(
    activity: Activity, baseline: Activity | dict
) -> tuple[bool, Optional[AssertionErrorData]]:
    """Asserts that the given activity matches the baseline activity.

    :param activity: The activity to be tested.
    :param baseline: The baseline activity or a dictionary representing the expected activity data.
    """
    actual_activity = normalize_activity_data(activity)
    baseline = normalize_activity_data(baseline)
    return _check(actual_activity, baseline, "activity")
