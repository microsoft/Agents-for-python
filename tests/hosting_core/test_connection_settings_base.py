# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import FrozenInstanceError, dataclass

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.connections import (
    ConnectionSettingsBase,
)


class TestConnectionSettingsBase:
    def test_defaults(self):
        settings = ConnectionSettingsBase.from_mapping({})

        assert settings.client_id is None
        assert settings.authority is None
        assert settings.tenant_id is None
        assert settings.scopes == []
        assert settings.alternate_blueprint_connection_name is None
        assert isinstance(settings.extras, Configuration)
        assert settings.extras == {}

    @pytest.mark.parametrize("wrapper", [None, "settings", "SETTINGS"])
    @pytest.mark.parametrize(
        "values",
        [
            {
                "client_id": "cid",
                "authority": "https://authority",
                "tenant_id": "tid",
                "scopes": ["s1"],
                "alternate_blueprint_connection_name": "bp",
            },
            {
                "CLIENTID": "cid",
                "AUTHORITYENDPOINT": "https://authority",
                "TENANTID": "tid",
                "SCOPES": ["s1"],
                "ALTERNATEBLUEPRINTCONNECTIONNAME": "bp",
            },
            {
                "CLIENT_ID": "cid",
                "AUTHORITY": "https://authority",
                "TENANT_ID": "tid",
                "SCOPES": ["s1"],
                "ALT_BLUEPRINT_ID": "bp",
            },
        ],
    )
    def test_binds_flat_and_wrapped_settings(self, values, wrapper):
        config = Configuration({wrapper: values} if wrapper else values)

        settings = ConnectionSettingsBase.from_configuration(config)

        assert settings.client_id == "cid"
        assert settings.authority == "https://authority"
        assert settings.tenant_id == "tid"
        assert settings.scopes == ["s1"]
        assert settings.alternate_blueprint_connection_name == "bp"

    def test_from_mapping_uses_keyword_arguments_as_defaults(self):
        settings = ConnectionSettingsBase.from_mapping(
            {"client_id": "primary"}, client_id="fallback", tenant_id="tid"
        )

        assert settings.client_id == "primary"
        assert settings.tenant_id == "tid"

    def test_from_configuration_reuses_bound_instance(self):
        settings = ConnectionSettingsBase(client_id="cid")

        assert ConnectionSettingsBase.from_configuration(settings) is settings

    def test_extras_preserve_unknown_fields_and_section_path(self):
        config = Configuration(
            {"CLIENTID": "cid", "CUSTOM": {"enabled": True}},
            _base_path="Service::SETTINGS",
        )

        settings = ConnectionSettingsBase.from_configuration(config)

        assert "CLIENTID" not in settings.extras
        assert settings.extras["CUSTOM"] == {"enabled": True}
        assert settings.extras._base_path == "Service::SETTINGS"

    def test_legacy_conversion_preserves_common_fields(self):
        with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
            legacy = AgentAuthConfiguration(
                client_id="cid", tenant_id="tid", scopes=["s1"], ALT_BLUEPRINT_NAME="bp"
            )

        settings = ConnectionSettingsBase._from_agent_auth_config(legacy)

        assert settings.client_id == "cid"
        assert settings.tenant_id == "tid"
        assert settings.scopes == ["s1"]
        assert settings.alternate_blueprint_connection_name == "bp"

    def test_subclass_fields_are_recognized_without_changing_base_fields(self):
        @dataclass(frozen=True)
        class CustomSettings(ConnectionSettingsBase):
            custom: str | None = None

            @classmethod
            def _get_init_kwargs(cls, config):
                return {
                    **super()._get_init_kwargs(config),
                    "custom": config.get_strn("custom"),
                }

        child = CustomSettings.from_mapping({"client_id": "cid", "custom": "value"})
        base = ConnectionSettingsBase.from_mapping({"custom": "value"})

        assert child.custom == "value"
        assert "custom" not in child.extras
        assert base.extras["custom"] == "value"

    def test_fields_are_frozen_but_nested_values_are_not(self):
        settings = ConnectionSettingsBase.from_mapping({"scopes": ["s1"], "CUSTOM": 1})

        with pytest.raises(FrozenInstanceError):
            settings.client_id = "changed"

        settings.scopes.append("s2")
        settings.extras["CUSTOM"] = 2
        assert settings.scopes == ["s1", "s2"]
        assert settings.extras["CUSTOM"] == 2

    def test_mutable_defaults_are_not_shared_between_instances(self):
        first = ConnectionSettingsBase()
        second = ConnectionSettingsBase()

        first.scopes.append("first")
        first.extras["CUSTOM"] = "first"

        assert second.scopes == []
        assert second.extras == {}

    def test_malformed_settings_section_is_not_treated_as_missing(self):
        with pytest.raises(TypeError, match="SETTINGS"):
            ConnectionSettingsBase.from_mapping({"SETTINGS": "not-a-mapping"})
