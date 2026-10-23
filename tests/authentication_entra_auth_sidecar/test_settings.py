# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core import AgentAuthConfiguration, ConnectionManager
from microsoft_agents.authentication.entra_auth_sidecar import SidecarAuth
from microsoft_agents.authentication.entra_auth_sidecar import (
    SidecarConnectionSettings,
)
from microsoft_agents.hosting.core.authorization.connections import (
    ConnectionSettingsBase,
)
from microsoft_agents.authentication.entra_auth_sidecar.errors import (
    SidecarAuthError,
)

import pytest


class TestScopeNormalization:
    def test_none(self):
        assert SidecarConnectionSettings._normalize_scopes(None) is None

    def test_list(self):
        assert SidecarConnectionSettings._normalize_scopes(["a", "b"]) == ["a", "b"]

    def test_space_delimited_string(self):
        assert SidecarConnectionSettings._normalize_scopes("a b") == ["a", "b"]

    def test_comma_delimited_string(self):
        assert SidecarConnectionSettings._normalize_scopes("a, b") == ["a", "b"]

    def test_dict_from_env_nesting(self):
        # Env "SCOPES__0=a", "SCOPES__1=b" parses into {"0": "a", "1": "b"}.
        assert SidecarConnectionSettings._normalize_scopes({"0": "a", "1": "b"}) == [
            "a",
            "b",
        ]

    def test_empty_collapses_to_none(self):
        assert SidecarConnectionSettings._normalize_scopes("") is None
        assert SidecarConnectionSettings._normalize_scopes([]) is None


class TestSettingsFromConfiguration:
    def test_reads_sidecar_settings_from_upper_case_kwargs(self):
        config = Configuration(
            client_id="blueprint-id",
            SERVICE_NAME="botframework",
            BLUEPRINT_SERVICE_NAME="bp",
            SIDECAR_BASE_URL="http://localhost:5178",
        )
        settings = SidecarConnectionSettings.from_configuration(config)
        assert settings.service_name == "botframework"
        assert settings.blueprint_service_name == "bp"
        assert settings.sidecar_base_url == "http://localhost:5178"

    def test_defaults_when_absent(self):
        config = Configuration(client_id="blueprint-id")
        settings = SidecarConnectionSettings.from_configuration(config)
        assert settings.service_name == "default"
        assert settings.blueprint_service_name == "agenticblueprint"

    def test_inherits_connection_settings_base(self):
        assert issubclass(SidecarConnectionSettings, ConnectionSettingsBase)

    def test_binds_base_fields_from_configuration(self):
        config = Configuration(
            client_id="blueprint-id",
            tenant_id="tenant-1",
            authority="https://authority",
            ALTERNATEBLUEPRINTCONNECTIONNAME="bp-conn",
        )
        settings = SidecarConnectionSettings.from_configuration(config)
        assert settings.client_id == "blueprint-id"
        assert settings.tenant_id == "tenant-1"
        assert settings.authority == "https://authority"
        assert settings.alternate_blueprint_connection_name == "bp-conn"

    def test_binds_from_raw_mapping(self):
        # A raw SETTINGS mapping (e.g. a parsed env dict) must bind both the base
        # fields (via the shared base helper) and the sidecar-specific fields,
        # not silently fall back to defaults.
        settings = SidecarConnectionSettings.from_mapping(
            {"SERVICE_NAME": "svc", "CLIENTID": "cid", "SCOPES": ["s"]}
        )
        assert settings.service_name == "svc"
        assert settings.client_id == "cid"
        assert settings.scopes == ["s"]


class TestAgentAuthConfigurationPreservesExtraSettings:
    @pytest.fixture(autouse=True)
    def deprecated_configuration_warning(self):
        with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
            yield

    def test_unknown_kwargs_preserved_in_provider_settings(self):
        config = AgentAuthConfiguration(
            auth_type="EntraAuthSideCar",
            SERVICE_NAME="botframework",
            SIDECAR_BASE_URL="http://localhost:5178",
        )
        assert config.provider_settings["SERVICE_NAME"] == "botframework"
        assert config.provider_settings["SIDECAR_BASE_URL"] == "http://localhost:5178"

    def test_recognized_core_keys_not_copied_into_provider_settings(self):
        config = AgentAuthConfiguration(
            auth_type="EntraAuthSideCar",
            CLIENTID="app-id",
            CLIENTSECRET="super-secret",
            TENANTID="tenant",
            SERVICE_NAME="botframework",
        )
        # Recognized core alias keys — including the client secret — must never
        # be duplicated into the provider bag (avoids leaking sensitive values).
        assert "CLIENTSECRET" not in config.provider_settings
        assert "CLIENTID" not in config.provider_settings
        assert "TENANTID" not in config.provider_settings
        # ...but they are still bound to their first-class fields.
        assert config.CLIENT_SECRET == "super-secret"
        assert config.CLIENT_ID == "app-id"
        # ...and genuinely provider-specific keys are still preserved.
        assert config.provider_settings["SERVICE_NAME"] == "botframework"


class TestEnvConfigEndToEnd:
    """Regression: sidecar settings must survive the env -> config -> provider flow."""

    def test_settings_flow_from_env(self):
        env = {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__AUTHTYPE": "EntraAuthSideCar",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "blueprint-id",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "tenant-1",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SERVICE_NAME": "botframework",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SIDECAR_BASE_URL": (
                "http://localhost:5178"
            ),
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SCOPES__0": "res/.default",
            "CONNECTIONSMAP__0__SERVICEURL": "*",
            "CONNECTIONSMAP__0__CONNECTION": "SERVICE_CONNECTION",
        }
        cfg = load_configuration_from_env(env)
        cm = ConnectionManager(provider_factory=SidecarAuth, config=cfg)
        settings = cm.get_default_connection().config
        assert settings.service_name == "botframework"
        assert settings.sidecar_base_url == "http://localhost:5178"
        assert settings.scopes == ["res/.default"]


class TestScalarCoercion:
    """Scalar settings must tolerate the string values produced by env config."""

    def test_bypass_false_string_keeps_protection_on(self):
        settings = SidecarConnectionSettings.from_mapping(
            bypass_local_network_restriction="false"
        )
        assert settings.bypass_local_network_restriction is False

    def test_bypass_true_string(self):
        settings = SidecarConnectionSettings.from_mapping(
            bypass_local_network_restriction="true"
        )
        assert settings.bypass_local_network_restriction is True

    @pytest.mark.parametrize("raw", ["0", "false", "False", "FALSE"])
    def test_bypass_falsy_strings(self, raw):
        settings = SidecarConnectionSettings.from_mapping(
            bypass_local_network_restriction=raw
        )
        assert settings.bypass_local_network_restriction is False

    @pytest.mark.parametrize("raw", ["1", "true", "True", "TRUE"])
    def test_bypass_truthy_strings(self, raw):
        settings = SidecarConnectionSettings.from_mapping(
            bypass_local_network_restriction=raw
        )
        assert settings.bypass_local_network_restriction is True

    @pytest.mark.parametrize("raw", ["maybe", "no", "off", "yes", "on"])
    def test_unrecognized_bypass_value_is_rejected(self, raw):
        with pytest.raises(ValueError, match="bypass_local_network_restriction"):
            SidecarConnectionSettings.from_mapping(bypass_local_network_restriction=raw)

    def test_blank_bypass_value_uses_default(self):
        settings = SidecarConnectionSettings.from_mapping(
            bypass_local_network_restriction=""
        )
        assert settings.bypass_local_network_restriction is False

    def test_retry_count_string_coerced_to_int(self):
        settings = SidecarConnectionSettings.from_mapping(retry_count="5")
        assert settings.retry_count == 5
        assert isinstance(settings.retry_count, int)

    def test_request_timeout_string_coerced_to_float(self):
        settings = SidecarConnectionSettings.from_mapping(request_timeout="45")
        assert settings.request_timeout == 45.0
        assert isinstance(settings.request_timeout, float)

    def test_blank_numeric_strings_fall_back_to_defaults(self):
        settings = SidecarConnectionSettings.from_mapping(
            retry_count="", request_timeout=""
        )
        assert settings.retry_count == 3
        assert settings.request_timeout == 30.0

    def test_invalid_retry_count_raises_clear_error(self):
        with pytest.raises(ValueError, match="RETRY_COUNT"):
            SidecarConnectionSettings.from_mapping({"RETRY_COUNT": "abc"})

    def test_invalid_request_timeout_raises_clear_error(self):
        with pytest.raises(ValueError, match="REQUEST_TIMEOUT"):
            SidecarConnectionSettings.from_mapping({"REQUEST_TIMEOUT": "abc"})


class TestEnvScalarFlowEndToEnd:
    """Scalars must survive env -> config -> provider with strings (regression)."""

    @staticmethod
    def _env(**overrides):
        env = {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__AUTHTYPE": "EntraAuthSideCar",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "blueprint-id",
            "CONNECTIONSMAP__0__SERVICEURL": "*",
            "CONNECTIONSMAP__0__CONNECTION": "SERVICE_CONNECTION",
        }
        env.update(overrides)
        return env

    def test_bypass_false_from_env_still_rejects_public_url(self):
        # The exact bug class: BYPASS="false" must NOT disable the SSRF guard.
        env = self._env(
            **{
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SIDECAR_BASE_URL": (
                    "http://example.com"
                ),
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__"
                "BYPASS_LOCAL_NETWORK_RESTRICTION": "false",
            }
        )
        cfg = load_configuration_from_env(env)
        with pytest.raises(SidecarAuthError):
            ConnectionManager(provider_factory=SidecarAuth, config=cfg)

    def test_bypass_true_from_env_allows_public_url(self):
        env = self._env(
            **{
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SIDECAR_BASE_URL": (
                    "http://example.com"
                ),
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__"
                "BYPASS_LOCAL_NETWORK_RESTRICTION": "true",
            }
        )
        cfg = load_configuration_from_env(env)
        cm = ConnectionManager(provider_factory=SidecarAuth, config=cfg)
        settings = cm.get_default_connection().config
        assert settings.bypass_local_network_restriction is True

    def test_retry_and_timeout_strings_construct_from_env(self):
        env = self._env(
            **{
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SIDECAR_BASE_URL": (
                    "http://localhost:5178"
                ),
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__RETRY_COUNT": "5",
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__REQUEST_TIMEOUT": "45",
            }
        )
        cfg = load_configuration_from_env(env)
        cm = ConnectionManager(provider_factory=SidecarAuth, config=cfg)
        settings = cm.get_default_connection().config
        assert settings.retry_count == 5
        assert settings.request_timeout == 45.0
        assert settings.bypass_local_network_restriction is False
