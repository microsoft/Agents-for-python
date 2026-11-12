# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config._engine._utils import (
    _parse_env_var_name,
    _resolve_keys_arg,
    str_in,
)


def test_environment_name_conversion_preserves_case_and_single_underscores():
    assert (
        _parse_env_var_name("Connections__SERVICE_CONNECTION__CLIENT_ID")
        == "Connections::SERVICE_CONNECTION::CLIENT_ID"
    )


def test_resolve_keys_flattens_lists_without_splitting_literal_strings():
    assert _resolve_keys_arg("A::B", ["C", "D"], [], "E") == ["A::B", "C", "D", "E"]


@pytest.mark.parametrize("value", [None, 1, ("A", "B")])
def test_resolve_keys_rejects_unsupported_argument_types(value):
    with pytest.raises(ValueError, match="Invalid key type"):
        _resolve_keys_arg(value)


def test_str_in_matches_any_substring_and_preserves_case_sensitivity():
    assert str_in("ServiceConnection", "Missing", "Connection")
    assert not str_in("ServiceConnection", "connection")
    assert not str_in("ServiceConnection")
