from os import environ
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import AgentAuthConfiguration, AuthTypes


class TestAuthorizationConfiguration:
    """
    Unit tests to validate Authorization Configuration cases
    """

    def test_auth_configuration_basic(self):
        # test AgentAuthConfiguration with manual insertion of fields
        auth_config = AgentAuthConfiguration(
            auth_type=AuthTypes.client_secret,
            tenant_id="test-tenant-id",
            client_id="test-client-id",
            client_secret="test-client-secret",
            cert_pfx_file="test-cert.pfx",
            connection_name="test-connection",
            authority="https://login.microsoftonline.com",
            scopes=["test-scope-1", "test-scope-2"],
        )

        assert auth_config.AUTH_TYPE == AuthTypes.client_secret
        assert auth_config.TENANT_ID == "test-tenant-id"
        assert auth_config.CLIENT_ID == "test-client-id"
        assert auth_config.CLIENT_SECRET == "test-client-secret"
        assert auth_config.CERT_PFX_FILE == "test-cert.pfx"
        assert auth_config.CONNECTION_NAME == "test-connection"
        assert auth_config.AUTHORITY == "https://login.microsoftonline.com"
        assert auth_config.SCOPES == ["test-scope-1", "test-scope-2"]
        assert auth_config.ISSUERS == [
            "https://api.botframework.com",
            "https://sts.windows.net/test-tenant-id/",
            "https://login.microsoftonline.com/test-tenant-id/v2.0",
        ]

    def test_load_configuration_from_env(self):
        # test load_configuration_from_env, passed to AgentAuthConfiguration
        mock_environ = {
            **environ,
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "test-tenant-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "test-client-id-SERVICE_CONNECTION",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": "test-client-secret-SERVICE_CONNECTION",
            "CONNECTIONS__MCS__SETTINGS__TENANTID": "test-tenant-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTID": "test-client-id-MCS",
            "CONNECTIONS__MCS__SETTINGS__CLIENTSECRET": "test-client-secret-MCS",
        }

        mock_config = load_configuration_from_env(mock_environ)

        raw_configurations: dict[str, dict] = mock_config.get("CONNECTIONS", {})

        for name, settings in raw_configurations.items():
            auth_config = AgentAuthConfiguration(**settings["SETTINGS"])
            assert auth_config.AUTH_TYPE == AuthTypes.client_secret
            assert auth_config.CLIENT_ID == f"test-client-id-{name}"
            assert auth_config.TENANT_ID == f"test-tenant-id-{name}"
            assert auth_config.CLIENT_SECRET == f"test-client-secret-{name}"
            assert auth_config.ISSUERS == [
                "https://api.botframework.com",
                f"https://sts.windows.net/test-tenant-id-{name}/",
                f"https://login.microsoftonline.com/test-tenant-id-{name}/v2.0",
            ]

    def test_issuer_list_from_env(self):
        mock_config = load_configuration_from_env(
            {
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ISSUERS__0": "https://issuer-one.example/",
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ISSUERS__1": "https://issuer-two.example/",
                "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__VALIDATE_ISSUER": "true",
            }
        )

        auth_config = AgentAuthConfiguration(
            **mock_config["CONNECTIONS"]["SERVICE_CONNECTION"]["SETTINGS"]
        )

        assert auth_config.ISSUERS == [
            "https://issuer-one.example/",
            "https://issuer-two.example/",
        ]
        assert auth_config.VALIDATE_ISSUER is True

    def test_scalar_issuer_string_is_single_entry(self):
        auth_config = AgentAuthConfiguration(
            ISSUERS="https://issuer.example/", VALIDATE_ISSUER="true"
        )

        assert auth_config.ISSUERS == ["https://issuer.example/"]

    def test_empty_settings(self):
        auth_config = AgentAuthConfiguration()
        assert auth_config.AUTH_TYPE == AuthTypes.client_secret
        assert auth_config.TENANT_ID is None
        assert auth_config.CLIENT_ID is None
        assert auth_config.CLIENT_SECRET is None
        assert auth_config.CERT_PFX_FILE is None
        assert auth_config.FEDERATED_CLIENT_ID is None
        assert auth_config.CONNECTION_NAME is None
        assert auth_config.AUTHORITY is None
        assert auth_config.SCOPES is None
        assert auth_config.AZURE_REGION is None

    def test_azure_region_from_parameter(self):
        auth_config = AgentAuthConfiguration(azure_region="westus")
        assert auth_config.AZURE_REGION == "westus"

    def test_azure_region_from_kwargs(self):
        auth_config = AgentAuthConfiguration(AZUREREGION="eastus")
        assert auth_config.AZURE_REGION == "eastus"

    def test_azure_region_legacy_regional_authority_fallback(self):
        # When AZUREREGION is not provided, fall back to the legacy
        # RegionalAuthority configuration key.
        auth_config = AgentAuthConfiguration(REGIONALAUTHORITY="westeurope")
        assert auth_config.AZURE_REGION == "westeurope"

    def test_azure_region_prefers_azure_region_over_legacy(self):
        auth_config = AgentAuthConfiguration(
            AZUREREGION="eastus", REGIONALAUTHORITY="westeurope"
        )
        assert auth_config.AZURE_REGION == "eastus"

    def test_idpm_resource_defaults_none(self):
        auth_config = AgentAuthConfiguration()
        assert auth_config.IDPM_RESOURCE is None

    def test_idpm_resource_from_parameter(self):
        auth_config = AgentAuthConfiguration(
            auth_type=AuthTypes.identity_proxy_manager,
            client_id="test-client-id",
            idpm_resource="https://custom-resource/.default",
        )
        assert auth_config.AUTH_TYPE == AuthTypes.identity_proxy_manager
        assert auth_config.IDPM_RESOURCE == "https://custom-resource/.default"

    def test_idpm_resource_from_kwargs(self):
        auth_config = AgentAuthConfiguration(
            IDPMRESOURCE="https://custom-resource/.default"
        )
        assert auth_config.IDPM_RESOURCE == "https://custom-resource/.default"

    def test_dotnet_aligned_property_aliases(self):
        # The snake_case aliases mirror the .NET ConnectionSettingsBase property
        # names and are thin read-only views over the UPPER_SNAKE attributes.
        auth_config = AgentAuthConfiguration(
            client_id="cid",
            tenant_id="tid",
            authority="https://login.microsoftonline.com",
            scopes=["s1"],
            ALT_BLUEPRINT_NAME="bp",
        )
        assert auth_config.client_id == "cid"
        assert auth_config.tenant_id == "tid"
        assert auth_config.authority == "https://login.microsoftonline.com"
        assert auth_config.scopes == ["s1"]
        assert auth_config.alternate_blueprint_connection_name == "bp"

    def test_authority_endpoint_alias_key(self):
        # .NET binds authority from "AuthorityEndpoint"; accept it as an alias.
        auth_config = AgentAuthConfiguration(AUTHORITYENDPOINT="https://authority")
        assert auth_config.AUTHORITY == "https://authority"
        assert auth_config.authority == "https://authority"

    def test_authority_key_preferred_over_authority_endpoint(self):
        auth_config = AgentAuthConfiguration(
            AUTHORITY="https://primary", AUTHORITYENDPOINT="https://secondary"
        )
        assert auth_config.AUTHORITY == "https://primary"

    def test_alternate_blueprint_connection_name_alias_key(self):
        # .NET names this "AlternateBlueprintConnectionName".
        auth_config = AgentAuthConfiguration(ALTERNATEBLUEPRINTCONNECTIONNAME="bp-conn")
        assert auth_config.ALT_BLUEPRINT_ID == "bp-conn"
        assert auth_config.alternate_blueprint_connection_name == "bp-conn"

    def test_alt_blueprint_name_key_preferred(self):
        auth_config = AgentAuthConfiguration(
            ALT_BLUEPRINT_NAME="legacy", ALTERNATEBLUEPRINTCONNECTIONNAME="new"
        )
        assert auth_config.ALT_BLUEPRINT_ID == "legacy"

    def test_anonymous_allowed_false_string_is_false(self):
        # Env values arrive as strings; bool("false") would be True and silently
        # enable anonymous auth. Coercion must yield False.
        auth_config = AgentAuthConfiguration(ANONYMOUS_ALLOWED="false")
        assert auth_config.ANONYMOUS_ALLOWED is False

    def test_anonymous_allowed_true_string_is_true(self):
        auth_config = AgentAuthConfiguration(ANONYMOUS_ALLOWED="true")
        assert auth_config.ANONYMOUS_ALLOWED is True

    def test_anonymous_allowed_default_is_false(self):
        assert AgentAuthConfiguration().ANONYMOUS_ALLOWED is False

    def test_anonymous_allowed_bool_param(self):
        assert AgentAuthConfiguration(anonymous_allowed=True).ANONYMOUS_ALLOWED is True

    def test_explicit_anonymous_allowed_false_overrides_kwarg(self):
        # An explicit anonymous_allowed=False must win over a truthy kwarg rather
        # than being treated as "unset" by an `or` fallback.
        auth_config = AgentAuthConfiguration(
            anonymous_allowed=False, ANONYMOUS_ALLOWED="true"
        )
        assert auth_config.ANONYMOUS_ALLOWED is False

    def test_anonymous_allowed_kwarg_used_when_param_unset(self):
        # When the constructor arg is not provided, the kwarg is honored.
        auth_config = AgentAuthConfiguration(ANONYMOUS_ALLOWED="true")
        assert auth_config.ANONYMOUS_ALLOWED is True

    def test_validate_issuer_default_false(self):
        assert AgentAuthConfiguration().VALIDATE_ISSUER is False

    def test_validate_issuer_true_bool_param(self):
        auth_config = AgentAuthConfiguration(validate_issuer=True)
        assert auth_config.VALIDATE_ISSUER is True

    def test_validate_issuer_false_string_kwarg_is_false(self):
        # Same fail-safe coercion as ANONYMOUS_ALLOWED: bool("false") would be
        # True and silently enable issuer validation when configured off.
        auth_config = AgentAuthConfiguration(VALIDATE_ISSUER="false")
        assert auth_config.VALIDATE_ISSUER is False

    def test_validate_issuer_true_string_kwarg_is_true(self):
        auth_config = AgentAuthConfiguration(VALIDATE_ISSUER="true")
        assert auth_config.VALIDATE_ISSUER is True

    def test_validate_issuer_explicit_false_overrides_kwarg(self):
        auth_config = AgentAuthConfiguration(
            validate_issuer=False, VALIDATE_ISSUER="true"
        )
        assert auth_config.VALIDATE_ISSUER is False

    def test_issuers_default_when_not_configured(self):
        auth_config = AgentAuthConfiguration(tenant_id="tenant-1")
        assert auth_config.ISSUERS == [
            "https://api.botframework.com",
            "https://sts.windows.net/tenant-1/",
            "https://login.microsoftonline.com/tenant-1/v2.0",
        ]

    def test_issuers_explicit_list_overrides_default(self):
        auth_config = AgentAuthConfiguration(
            tenant_id="tenant-1",
            issuers=["https://custom-issuer.example.com/"],
        )
        assert auth_config.ISSUERS == ["https://custom-issuer.example.com/"]

    def test_issuers_kwarg_alias(self):
        auth_config = AgentAuthConfiguration(
            tenant_id="tenant-1", ISSUERS=["https://custom-issuer.example.com/"]
        )
        assert auth_config.ISSUERS == ["https://custom-issuer.example.com/"]

    def test_issuers_param_preferred_over_kwarg(self):
        auth_config = AgentAuthConfiguration(
            tenant_id="tenant-1",
            issuers=["https://primary.example.com/"],
            ISSUERS=["https://secondary.example.com/"],
        )
        assert auth_config.ISSUERS == ["https://primary.example.com/"]

    def test_issuers_default_uses_gov_cloud_when_authority_is_gov(self):
        auth_config = AgentAuthConfiguration(
            tenant_id="tenant-1", authority="https://login.microsoftonline.us"
        )
        assert auth_config.ISSUERS == [
            "https://api.botframework.us",
            "https://sts.windows.net/tenant-1/",
            "https://login.microsoftonline.us/tenant-1/v2.0",
        ]

    def test_issuers_default_uses_authority_embedded_common_tenant(self):
        # The authority-embedded tenant segment takes precedence over a
        # separately configured (concrete) TENANT_ID, matching the JS
        # reference's getEffectiveTenant/resolveAuthority precedence.
        auth_config = AgentAuthConfiguration(
            tenant_id="concrete-tenant-id",
            authority="https://login.microsoftonline.com/common",
        )
        assert auth_config.ISSUERS == [
            "https://api.botframework.com",
            "https://sts.windows.net/common/",
            "https://login.microsoftonline.com/common/v2.0",
        ]

    def test_issuers_default_uses_authority_embedded_concrete_tenant(self):
        # A concrete tenant embedded in AUTHORITY must be used instead of a
        # "common"/absent TENANT_ID, avoiding an incorrect "/common" or
        # "/None" default issuer.
        auth_config = AgentAuthConfiguration(
            tenant_id="common",
            authority="https://login.microsoftonline.com/concrete-tenant-id",
        )
        assert auth_config.ISSUERS == [
            "https://api.botframework.com",
            "https://sts.windows.net/concrete-tenant-id/",
            "https://login.microsoftonline.com/concrete-tenant-id/v2.0",
        ]

    def test_issuers_default_falls_back_to_common_without_tenant_id_or_authority_path(
        self,
    ):
        # Neither TENANT_ID nor an authority-embedded tenant segment is
        # configured: the default must fall back to "common" rather than
        # embedding a literal "None" in the issuer URLs.
        auth_config = AgentAuthConfiguration(
            authority="https://login.microsoftonline.com"
        )
        assert auth_config.ISSUERS == [
            "https://api.botframework.com",
            "https://sts.windows.net/common/",
            "https://login.microsoftonline.com/common/v2.0",
        ]

    def test_issuers_and_validate_issuer_not_in_provider_settings(self):
        # Recognized keys (bound into first-class fields) must never be
        # duplicated into the provider-specific settings bag.
        auth_config = AgentAuthConfiguration(
            ISSUERS=["https://custom-issuer.example.com/"],
            VALIDATE_ISSUER="true",
            SOME_PROVIDER_KEY="keep-me",
        )
        assert "ISSUERS" not in auth_config.provider_settings
        assert "VALIDATE_ISSUER" not in auth_config.provider_settings
        assert auth_config.provider_settings == {"SOME_PROVIDER_KEY": "keep-me"}

    def test_jwt_patch_is_valid_aud_rejects_non_string_audience(self):
        # A non-string `aud` (e.g. the JWT-spec-permitted array form, or a
        # malformed numeric/object claim) must be reported as invalid rather
        # than raising AttributeError from `.lower()` on a non-string value.
        auth_config = AgentAuthConfiguration(client_id="client-1")
        assert auth_config._jwt_patch_is_valid_aud(["client-1"]) is False
        assert auth_config._jwt_patch_is_valid_aud(12345) is False
        assert auth_config._jwt_patch_is_valid_aud({"aud": "client-1"}) is False
        # Sanity check: normal string behavior is unaffected.
        assert auth_config._jwt_patch_is_valid_aud("client-1") is True

    def test_jwt_patch_find_connection_treats_non_string_audience_as_no_match(self):
        # Routing must not raise on a non-string `aud`; it should behave as
        # "no matching connection" so callers fall back to default routing.
        auth_config = AgentAuthConfiguration(client_id="client-1")
        assert auth_config._jwt_patch_find_connection(["client-1"]) is None
        assert auth_config._jwt_patch_find_connection(12345) is None
        assert auth_config._jwt_patch_find_connection({"aud": "client-1"}) is None
        # Sanity check: normal string behavior is unaffected.
        assert auth_config._jwt_patch_find_connection("client-1") is auth_config
