# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from microsoft_agents.activity import AgentsModel

from .type_defs import FieldAssertionType
from .check_model import check_model_verbose
from .check_field import check_field_verbose


def assert_field(
    actual_value: Any, assertion: Any, assertion_type: FieldAssertionType
) -> None:
    """Asserts that a specific field in the target matches the baseline.

    :param key_in_baseline: The key of the field to be tested.
    :param target: The target dictionary containing the actual values.
    :param assertion: The baseline dictionary containing the expected values.
    """
    res, assertion_error_message = check_field_verbose(
        actual_value, assertion, assertion_type
    )
    assert res, assertion_error_message


def assert_model(model: AgentsModel | dict, assertion: AgentsModel | dict) -> None:
    """Asserts that the given model matches the baseline model.

    :param model: The model to be tested.
    :param assertion: The baseline model or a dictionary representing the expected model data.
    """
    res, assertion_error_data = check_model_verbose(model, assertion)
    assert res, str(assertion_error_data)
