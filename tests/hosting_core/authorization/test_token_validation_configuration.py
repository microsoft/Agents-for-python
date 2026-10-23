# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.jwt.jwt_connection_settings import (
    JwtConnectionSettings,
)
from microsoft_agents.hosting.core.authorization.jwt.jwt_token_validator import (
    JwtTokenValidator,
)
from microsoft_agents.hosting.core.authorization.jwt.token_validation_configuration import (
    TokenValidationConfiguration,
)


def _root(**token_validation):
    return Configuration(
        {
            "connections": {
                "SERVICE_CONNECTION": {
                    "settings": {
                        "client_id": "service-client",
                        "tenant_id": "service-tenant",
                        "anonymous_allowed": True,
                    }
                },
                "MCS": {
                    "settings": {"client_id": "mcs-client", "tenant_id": "mcs-tenant"}
                },
            },
            "token_validation": token_validation,
        }
    )


def test_absent_policy_uses_service_connection_and_all_connection_audiences():
    root = _root()
    del root["token_validation"]

    policy = TokenValidationConfiguration.from_configuration(root)

    assert policy.tenant_id == "service-tenant"
    assert policy.audiences == ["service-client", "mcs-client"]
    assert policy.anonymous_allowed is True
    assert isinstance(policy.connections["MCS"], JwtConnectionSettings)
    assert policy.default_jwt_settings is policy.connections["SERVICE_CONNECTION"]


@pytest.mark.parametrize(
    "values", [["explicit-1", "explicit-2"], {"0": "explicit-1", "1": "explicit-2"}]
)
def test_plural_audiences_override_connection_audiences(values):
    policy = TokenValidationConfiguration.from_configuration(_root(audiences=values))

    assert policy.audiences == ["explicit-1", "explicit-2"]
    assert policy.validate_audience("explicit-1") is True
    assert policy.validate_audience("service-client") is False


def test_environment_policy_and_connections_bind_together():
    root = load_configuration_from_env(
        {
            "TOKENVALIDATION__AUDIENCES__0": "explicit-client",
            "TOKENVALIDATION__TENANTID": "explicit-tenant",
            "TOKENVALIDATION__ANONYMOUSALLOWED": "false",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "service-client",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUSALLOWED": "true",
        }
    )

    policy = TokenValidationConfiguration.from_configuration(root)

    assert policy.audiences == ["explicit-client"]
    assert policy.tenant_id == "explicit-tenant"
    assert policy.anonymous_allowed is False
    assert policy.default_jwt_settings.anonymous_allowed is True


def test_explicit_false_overrides_anonymous_service_connection():
    policy = TokenValidationConfiguration.from_configuration(
        _root(anonymous_allowed=False)
    )

    assert policy.anonymous_allowed is False


def test_explicit_tenant_overrides_service_connection_tenant():
    policy = TokenValidationConfiguration.from_configuration(
        _root(tenant_id="explicit")
    )

    assert policy.tenant_id == "explicit"
    assert policy.default_jwt_settings.tenant_id == "service-tenant"


def test_empty_configuration_produces_no_audiences_or_anonymous_access():
    policy = TokenValidationConfiguration.from_mapping({})

    assert policy.audiences == []
    assert policy.connections == {}
    assert policy.default_jwt_settings is None
    assert policy.tenant_id is None
    assert policy.anonymous_allowed is False


def test_audience_matching_and_routing_are_case_insensitive():
    policy = TokenValidationConfiguration.from_configuration(_root())

    assert policy.validate_audience("MCS-CLIENT") is True
    assert policy.get_connection_settings("MCS-CLIENT") is policy.connections["MCS"]
    assert policy.get_connection_settings("unmatched") is policy.default_jwt_settings


@pytest.mark.parametrize(
    "audience", [None, "", [], ["mcs-client"], 123, {"aud": "mcs-client"}]
)
def test_malformed_audiences_are_not_matched_or_routed(audience):
    policy = TokenValidationConfiguration.from_configuration(_root())

    assert policy.validate_audience(audience) is False
    assert policy.get_connection_settings(audience) is None


def test_jwt_validator_retains_supported_single_legacy_configuration():
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
        legacy = AgentAuthConfiguration(
            client_id="legacy-client", tenant_id="legacy-tenant", anonymous_allowed=True
        )

    policy = JwtTokenValidator(legacy).config

    assert policy.audiences == ["legacy-client"]
    assert policy.tenant_id == "legacy-tenant"
    assert policy.anonymous_allowed is True
