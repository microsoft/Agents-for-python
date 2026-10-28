# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

import pytest

from microsoft_agents.activity.config._logging._logging_configuration import (
    _LoggingConfiguration,
)


def test_missing_logging_configuration_has_no_level_entries():
    assert _LoggingConfiguration.from_mapping({}).log_levels == []


@pytest.mark.parametrize("key", ["log_level", "LOG_LEVEL", "LOGLEVEL"])
def test_logging_level_aliases_bind_namespace_and_level(key):
    settings = _LoggingConfiguration.from_mapping({key: {"My.Namespace": "debug"}})

    assert len(settings.log_levels) == 1
    assert settings.log_levels[0].namespace == "my.namespace"
    assert settings.log_levels[0].level == logging.DEBUG


@pytest.mark.parametrize("value", ["DEBUG", [], 1])
def test_non_mapping_log_levels_are_rejected(value):
    with pytest.raises(ValueError):
        _LoggingConfiguration.from_mapping({"LOGLEVEL": value})


def test_unrecognized_log_level_is_rejected():
    with pytest.raises(ValueError):
        _LoggingConfiguration.from_mapping({"LOGLEVEL": {"default": "not-a-level"}})
