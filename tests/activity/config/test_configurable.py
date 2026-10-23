# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from types import MappingProxyType

import pytest

from microsoft_agents.activity.config import Configuration, _Configurable


@dataclass(frozen=True)
class ApplicationSettings(_Configurable):
    enabled: bool
    count: int

    @classmethod
    def _from_configuration(cls, config: Configuration):
        return cls(
            enabled=config.get_bool("enabled", default=False),
            count=config.get_int("count", default=0),
        )


def test_binds_a_configuration_section():
    root = Configuration({"app": {"enabled": "true", "count": "4"}})

    settings = ApplicationSettings.from_configuration(root.get_section("app"))

    assert settings == ApplicationSettings(enabled=True, count=4)


def test_from_mapping_accepts_read_only_mappings_and_defaults():
    source = MappingProxyType({"enabled": "false"})

    settings = ApplicationSettings.from_mapping(source, enabled=True, count=3)

    assert settings == ApplicationSettings(enabled=False, count=3)
    assert dict(source) == {"enabled": "false"}


def test_from_configuration_reuses_bound_instances():
    settings = ApplicationSettings(enabled=True, count=2)

    assert ApplicationSettings.from_configuration(settings) is settings


@pytest.mark.parametrize("value", [{}, None, "invalid", 3])
def test_from_configuration_rejects_unbound_values(value):
    with pytest.raises(TypeError, match="ApplicationSettings"):
        ApplicationSettings.from_configuration(value)


def test_binding_preserves_section_paths_in_conversion_errors():
    root = Configuration({"app": {"count": "synthetic-secret"}})

    with pytest.raises(ValueError, match="app::count") as error:
        ApplicationSettings.from_configuration(root.get_section("app"))

    assert "synthetic-secret" not in str(error.value)
