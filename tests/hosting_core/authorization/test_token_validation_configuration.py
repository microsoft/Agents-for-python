# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import Configuration, _resolve
from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization.jwt import (
    JwtTokenValidator,
    TokenValidationConfiguration,
)

from tests._common.jwt_test_utils import generate_rsa_keypair, make_signed_jwt


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
    assert policy.default_jwt_settings is policy.connections["SERVICE_CONNECTION"]
    assert policy.get_connection_settings("MCS-CLIENT") is policy.connections["MCS"]
    assert policy.get_connection_settings("unmatched") is policy.default_jwt_settings


@pytest.mark.parametrize("values", [["explicit-client"], {"0": "explicit-client"}])
def test_explicit_policy_overrides_connection_defaults(values):
    policy = TokenValidationConfiguration.from_configuration(
        _root(audiences=values, tenant_id="explicit-tenant", anonymous_allowed=False)
    )
    assert policy.audiences == ["explicit-client"]
    assert policy.validate_audience("EXPLICIT-CLIENT")
    assert not policy.validate_audience("service-client")
    assert policy.tenant_id == "explicit-tenant"
    assert policy.anonymous_allowed is False


@pytest.mark.parametrize("audience", [None, "", [], ["mcs-client"], 123, {}])
def test_malformed_audiences_are_not_matched_or_routed(audience):
    policy = TokenValidationConfiguration.from_configuration(_root())
    assert policy.validate_audience(audience) is False
    assert policy.get_connection_settings(audience) is None


def test_legacy_configuration_preserves_explicit_issuer_policy():
    legacy = AgentAuthConfiguration(
        client_id="legacy-client",
        tenant_id="legacy-tenant",
        anonymous_allowed=True,
        validate_issuer=True,
        issuers=["https://custom.example.com/"],
    )
    policy = JwtTokenValidator(legacy).config
    assert policy.audiences == ["legacy-client"]
    assert policy.tenant_id == "legacy-tenant"
    assert policy.anonymous_allowed is True
    assert policy.default_jwt_settings.validate_issuer is True
    assert policy.default_jwt_settings.issuers == ["https://custom.example.com/"]


@pytest.mark.asyncio
async def test_configuration_based_validator_checks_signature_and_explicit_audience(
    monkeypatch,
):
    private_key, public_key = generate_rsa_keypair()
    validator = JwtTokenValidator(_root(audiences=["explicit-client"]))
    uris = []

    async def get_signing_key(uri, header):
        uris.append(uri)
        return public_key

    monkeypatch.setattr(
        validator._jwk_client_manager, "get_signing_key", get_signing_key
    )
    token = make_signed_jwt(private_key, {"aud": "explicit-client"})
    assert (await validator.validate_token(token)).claims["aud"] == "explicit-client"
    assert uris == [
        "https://login.microsoftonline.com/service-tenant/discovery/v2.0/keys"
    ]
    with pytest.raises(ValueError, match="Invalid audience"):
        await validator.validate_token(
            make_signed_jwt(private_key, {"aud": "service-client"})
        )


@pytest.mark.asyncio
async def test_empty_configuration_rejects_tokens_without_jwks_lookup(monkeypatch):
    private_key, _ = generate_rsa_keypair()
    validator = JwtTokenValidator(Configuration())

    async def unexpected_lookup(uri, header):
        pytest.fail("A configuration without routing settings must not fetch keys")

    monkeypatch.setattr(
        validator._jwk_client_manager, "get_signing_key", unexpected_lookup
    )
    with pytest.raises(ValueError, match="Invalid audience"):
        await validator.validate_token(make_signed_jwt(private_key, {"aud": "client"}))


def test_normalized_environment_policy_overrides_service_defaults():
    config = Configuration(
        _resolve(
            {
                "TOKENVALIDATION__AUDIENCES__10": "client-10",
                "TOKENVALIDATION__AUDIENCES__2": "client-2",
                "TOKENVALIDATION__TENANTID": "explicit-tenant",
                "TOKENVALIDATION__ANONYMOUSALLOWED": "false",
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "service-client",
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUSALLOWED": "true",
            }
        )
    )
    policy = TokenValidationConfiguration.from_configuration(config)
    assert policy.audiences == ["client-2", "client-10"]
    assert policy.tenant_id == "explicit-tenant"
    assert policy.anonymous_allowed is False
    assert policy.default_jwt_settings.anonymous_allowed is True


def test_no_service_connection_has_no_default_route_or_inherited_anonymous_access():
    config = _root()
    del config["connections"]["SERVICE_CONNECTION"]
    config["connections"]["MCS"]["settings"]["anonymous_allowed"] = True
    policy = TokenValidationConfiguration.from_configuration(config)
    assert policy.audiences == ["mcs-client"]
    assert policy.tenant_id is None
    assert policy.anonymous_allowed is False
    assert policy.default_jwt_settings is None
    assert policy.get_connection_settings("mcs-client") is policy.connections["MCS"]
    assert policy.get_connection_settings("unknown") is None


@pytest.mark.parametrize(
    "config, path, error_type",
    [
        ({"token_validation": "invalid"}, "token_validation", TypeError),
        ({"connections": []}, "connections", TypeError),
        ({"connections": {"MCS": "invalid"}}, "connections::MCS", TypeError),
        (
            {"connections": {"MCS": {"settings": []}}},
            "connections::MCS::settings",
            TypeError,
        ),
        (
            {"token_validation": {"anonymous_allowed": "invalid"}},
            "token_validation::anonymous_allowed",
            ValueError,
        ),
        (
            {"connections": {"MCS": {"settings": {"validate_issuer": "invalid"}}}},
            "connections::MCS::settings::validate_issuer",
            ValueError,
        ),
        (
            {"connections": {"MCS": {"settings": {"anonymous_allowed": "invalid"}}}},
            "connections::MCS::settings::anonymous_allowed",
            ValueError,
        ),
    ],
)
def test_invalid_configuration_reports_full_path(config, path, error_type):
    with pytest.raises(error_type) as error:
        TokenValidationConfiguration.from_mapping(config)
    assert path in str(error.value)
    assert "invalid" not in str(error.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("with_connection", [False, True])
async def test_missing_routing_settings_reject_before_fetching_keys(
    monkeypatch, with_connection
):
    config = Configuration(token_validation={"audiences": ["explicit-client"]})
    if with_connection:
        config["connections"] = {"MCS": {"settings": {"client_id": "mcs-client"}}}
    validator = JwtTokenValidator(config)
    assert validator.config.validate_audience("explicit-client")
    private_key, _ = generate_rsa_keypair()

    async def unexpected_lookup(uri, header):
        pytest.fail("An unmatched audience without a default route must not fetch keys")

    monkeypatch.setattr(
        validator._jwk_client_manager, "get_signing_key", unexpected_lookup
    )
    with pytest.raises(ValueError, match="Invalid audience"):
        await validator.validate_token(
            make_signed_jwt(private_key, {"aud": "explicit-client"})
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cloud, issuer_cloud, validate_issuer, mismatch_tid, accepted",
    [
        ("com", "com", True, False, True),
        ("us", "us", True, False, True),
        ("us", "com", True, False, False),
        ("com", "com", True, True, False),
        ("com", "com", False, True, False),
    ],
)
async def test_configuration_path_routes_and_validates_matched_connection(
    monkeypatch, cloud, issuer_cloud, validate_issuer, mismatch_tid, accepted
):
    service_tenant = "11111111-1111-1111-1111-111111111111"
    matched_tenant = "22222222-2222-2222-2222-222222222222"
    config = _root()
    config["connections"]["SERVICE_CONNECTION"]["settings"].update(
        tenant_id=service_tenant, validate_issuer=True
    )
    config["connections"]["MCS"]["settings"].update(
        tenant_id=matched_tenant,
        authority=f"https://login.microsoftonline.{cloud}",
        validate_issuer=validate_issuer,
    )
    validator = JwtTokenValidator(config)
    private_key, public_key = generate_rsa_keypair()
    uris = []

    async def get_signing_key(uri, header):
        uris.append(uri)
        return public_key

    monkeypatch.setattr(
        validator._jwk_client_manager, "get_signing_key", get_signing_key
    )
    token = make_signed_jwt(
        private_key,
        {
            "aud": "MCS-CLIENT",
            "iss": f"https://login.microsoftonline.{issuer_cloud}/{matched_tenant}/v2.0",
            "tid": service_tenant if mismatch_tid else matched_tenant,
        },
    )
    if accepted:
        identity = await validator.validate_token(token)
        assert identity.claims["aud"] == "MCS-CLIENT"
        assert identity.allow_anonymous is False
    else:
        with pytest.raises(ValueError, match="Invalid issuer"):
            await validator.validate_token(token)
    expected_tenant = matched_tenant if cloud == "us" else service_tenant
    assert uris == [
        f"https://login.microsoftonline.{cloud}/{expected_tenant}/discovery/v2.0/keys"
    ]
