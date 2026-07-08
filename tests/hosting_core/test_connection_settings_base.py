# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import (
    AgentAuthConfiguration,
    ConnectionSettingsBase,
)


class TestConnectionSettingsBase:
    """Validate the provider-agnostic base settings and its binding helpers."""

    def test_defaults_are_none(self):
        settings = ConnectionSettingsBase()
        assert settings.client_id is None
        assert settings.authority is None
        assert settings.tenant_id is None
        assert settings.scopes is None
        assert settings.alternate_blueprint_connection_name is None

    def test_explicit_values(self):
        settings = ConnectionSettingsBase(
            client_id="cid",
            authority="https://authority",
            tenant_id="tid",
            scopes=["s1", "s2"],
            alternate_blueprint_connection_name="bp",
        )
        assert settings.client_id == "cid"
        assert settings.authority == "https://authority"
        assert settings.tenant_id == "tid"
        assert settings.scopes == ["s1", "s2"]
        assert settings.alternate_blueprint_connection_name == "bp"

    def test_from_configuration_binds_base_fields(self):
        config = AgentAuthConfiguration(
            client_id="cid",
            tenant_id="tid",
            authority="https://authority",
            scopes=["s1"],
            ALT_BLUEPRINT_NAME="bp",
        )
        settings = ConnectionSettingsBase.from_configuration(config)
        assert settings.client_id == "cid"
        assert settings.tenant_id == "tid"
        assert settings.authority == "https://authority"
        assert settings.scopes == ["s1"]
        assert settings.alternate_blueprint_connection_name == "bp"

    def test_base_kwargs_from_configuration_reads_dotnet_aliases(self):
        config = AgentAuthConfiguration(
            CLIENTID="cid",
            AUTHORITYENDPOINT="https://authority",
            ALTERNATEBLUEPRINTCONNECTIONNAME="bp",
        )
        kwargs = ConnectionSettingsBase.base_kwargs_from_configuration(config)
        assert kwargs["client_id"] == "cid"
        assert kwargs["authority"] == "https://authority"
        assert kwargs["alternate_blueprint_connection_name"] == "bp"

    def test_from_configuration_binds_from_mapping(self):
        # A raw mapping (e.g. a parsed SETTINGS dict) must bind the same way an
        # attribute-style AgentAuthConfiguration does.
        config = {
            "CLIENT_ID": "cid",
            "AUTHORITY": "https://authority",
            "TENANT_ID": "tid",
            "SCOPES": ["s1"],
            "ALT_BLUEPRINT_ID": "bp",
        }
        settings = ConnectionSettingsBase.from_configuration(config)
        assert settings.client_id == "cid"
        assert settings.authority == "https://authority"
        assert settings.tenant_id == "tid"
        assert settings.scopes == ["s1"]
        assert settings.alternate_blueprint_connection_name == "bp"

    def test_from_configuration_binds_from_env_style_mapping(self):
        # load_configuration_from_env yields SETTINGS keys without underscores
        # (CLIENTID/TENANTID/AUTHORITYENDPOINT/ALTERNATEBLUEPRINTCONNECTIONNAME);
        # binding from such a raw mapping must not silently drop those values.
        config = {
            "CLIENTID": "cid",
            "AUTHORITYENDPOINT": "https://authority",
            "TENANTID": "tid",
            "SCOPES": ["s1"],
            "ALTERNATEBLUEPRINTCONNECTIONNAME": "bp",
        }
        settings = ConnectionSettingsBase.from_configuration(config)
        assert settings.client_id == "cid"
        assert settings.authority == "https://authority"
        assert settings.tenant_id == "tid"
        assert settings.scopes == ["s1"]
        assert settings.alternate_blueprint_connection_name == "bp"
