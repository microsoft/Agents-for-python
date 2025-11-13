# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from microsoft_agents.activity import Activity

from .type_defs import FieldAssertionType
from .check_activity import check_activity_verbose
from .check_field import check_field_verbose


def assert_activity(activity: Activity, assertion: Activity | dict) -> None:
    """Asserts that the given activity matches the baseline activity.

    :param activity: The activity to be tested.
    :param assertion: The baseline activity or a dictionary representing the expected activity data.
    """
    res, assertion_error_data = check_activity_verbose(activity, assertion)
    assert res, str(assertion_error_data)


def assert_field(
    actual_value: Any, assertion: Any, assertion_type: FieldAssertionType
) -> None:
    """Asserts that a specific field in the target matches the baseline.

    :param key_in_baseline: The key of the field to be tested.
    :param target: The target dictionary containing the actual values.
    :param assertion: The baseline dictionary containing the expected values.
    """
    res, assertion_error_message = check_field_verbose(actual_value, assertion, assertion_type)
    assert res, assertion_error_message