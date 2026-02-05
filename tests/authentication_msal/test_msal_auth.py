import pytest
from msal import ManagedIdentityClient, ConfidentialClientApplication

from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.core import Connections
from microsoft_agents.hosting.core.authorization import (
    AgentAuthConfiguration,
    AuthTypes,
)

from tests._common.testing_objects import MockMsalAuth


class TestMsalAuth:
    """
    Test suite for testing MsalAuth functionality
    """

    @pytest.mark.asyncio
    async def test_get_access_token_managed_identity(self, mocker):
        mock_auth = MockMsalAuth(mocker, ManagedIdentityClient)
        token = await mock_auth.get_access_token(
            "https://test.api.botframework.com", scopes=["test-scope"]
        )

        assert token == "token"
        mock_auth.mock_client.acquire_token_for_client.assert_called_with(
            resource="https://test.api.botframework.com"
        )

    @pytest.mark.asyncio
    async def test_get_access_token_confidential(self, mocker):
        mock_auth = MockMsalAuth(mocker, ConfidentialClientApplication)
        token = await mock_auth.get_access_token(
            "https://test.api.botframework.com", scopes=["test-scope"]
        )

        assert token == "token"
        mock_auth.mock_client.acquire_token_for_client.assert_called_with(
            scopes=["test-scope"]
        )

    @pytest.mark.asyncio
    async def test_acquire_token_on_behalf_of_managed_identity(self, mocker):
        mock_auth = MockMsalAuth(mocker, ManagedIdentityClient)

        try:
            await mock_auth.acquire_token_on_behalf_of(
                scopes=["test-scope"], user_assertion="test-assertion"
            )
        except NotImplementedError:
            assert True
        else:
            assert False

    @pytest.mark.asyncio
    async def test_acquire_token_on_behalf_of_confidential(self, mocker):
        mock_auth = MockMsalAuth(mocker, ConfidentialClientApplication)

        token = await mock_auth.acquire_token_on_behalf_of(
            scopes=["test-scope"], user_assertion="test-assertion"
        )

        assert token == "token"
        mock_auth.mock_client.acquire_token_on_behalf_of.assert_called_with(
            scopes=["test-scope"], user_assertion="test-assertion"
        )


class TestMsalAuthTenantResolution:
    """
    Test suite for testing tenant resolution methods in MsalAuth.
    These methods are critical for multi-tenant authentication support.
    """

    def test_resolve_tenant_id_with_override_parameter(self):
        """Test that tenant_id parameter takes precedence when provided"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc"
        )
        result = MsalAuth._resolve_tenant_id(config, "tenant-override")
        assert result == "tenant-override"

    def test_resolve_tenant_id_with_common_and_tenant_parameter(self):
        """Test that tenant_id parameter is used when config.TENANT_ID is 'common'"""
        config = AgentAuthConfiguration(tenant_id="common")
        result = MsalAuth._resolve_tenant_id(config, "specific-tenant")
        assert result == "specific-tenant"

    def test_resolve_tenant_id_with_common_no_tenant_parameter(self):
        """Test that None is returned when config.TENANT_ID is 'common' and no tenant_id provided"""
        config = AgentAuthConfiguration(tenant_id="common")
        result = MsalAuth._resolve_tenant_id(config, None)
        assert result is None

    def test_resolve_tenant_id_with_specific_tenant(self):
        """Test that config.TENANT_ID is returned when it's a specific value"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc"
        )
        result = MsalAuth._resolve_tenant_id(config, None)
        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_resolve_tenant_id_no_config_tenant_with_parameter(self):
        """Test that tenant_id parameter is used when config.TENANT_ID is not set.
        Note: tenant_id can be any string, not just GUID format."""
        config = AgentAuthConfiguration()
        result = MsalAuth._resolve_tenant_id(config, "fallback-tenant")
        assert result == "fallback-tenant"

    def test_resolve_tenant_id_no_config_tenant_no_parameter(self):
        """Test that ValueError is raised when neither config.TENANT_ID nor tenant_id are set"""
        config = AgentAuthConfiguration()
        with pytest.raises(
            ValueError, match="TENANT_ID is not set in the configuration"
        ):
            MsalAuth._resolve_tenant_id(config, None)

    def test_resolve_authority_with_common_replacement(self):
        """Test that /common is replaced with the resolved tenant_id in authority URL"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc",
            authority="https://login.microsoftonline.com/common",
        )
        result = MsalAuth._resolve_authority(config, None)
        assert (
            result
            == "https://login.microsoftonline.com/12345678-1234-1234-1234-123456789abc"
        )

    def test_resolve_authority_with_tenant_guid_replacement(self):
        """Test that existing tenant GUID is replaced with new tenant_id in authority URL"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc",
            authority="https://login.microsoftonline.com/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )
        result = MsalAuth._resolve_authority(
            config, "new-tenant-11111111-2222-3333-4444-555555555555"
        )
        assert (
            result
            == "https://login.microsoftonline.com/new-tenant-11111111-2222-3333-4444-555555555555"
        )

    def test_resolve_authority_with_common_and_tenant_parameter(self):
        """Test that /common is replaced with provided tenant_id parameter"""
        config = AgentAuthConfiguration(
            tenant_id="common", authority="https://login.microsoftonline.com/common"
        )
        result = MsalAuth._resolve_authority(
            config, "override-22222222-3333-4444-5555-666666666666"
        )
        assert (
            result
            == "https://login.microsoftonline.com/override-22222222-3333-4444-5555-666666666666"
        )

    def test_resolve_authority_no_authority_configured(self):
        """Test fallback to default URL when no authority is configured"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc"
        )
        result = MsalAuth._resolve_authority(config, None)
        assert (
            result
            == "https://login.microsoftonline.com/12345678-1234-1234-1234-123456789abc"
        )

    def test_resolve_authority_no_authority_with_tenant_override(self):
        """Test fallback to default URL with tenant override when no authority is configured"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc"
        )
        result = MsalAuth._resolve_authority(
            config, "override-99999999-8888-7777-6666-555555555555"
        )
        assert (
            result
            == "https://login.microsoftonline.com/override-99999999-8888-7777-6666-555555555555"
        )

    def test_resolve_authority_with_common_no_tenant_parameter(self):
        """Test behavior when config.TENANT_ID is 'common' and no tenant_id parameter"""
        config = AgentAuthConfiguration(
            tenant_id="common", authority="https://login.microsoftonline.com/common"
        )
        # When tenant_id is None after resolution, should return original authority
        result = MsalAuth._resolve_authority(config, None)
        assert result == "https://login.microsoftonline.com/common"

    def test_resolve_authority_regex_with_trailing_slash(self):
        """Test that regex correctly handles authority URLs with trailing slashes"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc",
            authority="https://login.microsoftonline.com/common/",
        )
        result = MsalAuth._resolve_authority(config, None)
        assert (
            result
            == "https://login.microsoftonline.com/12345678-1234-1234-1234-123456789abc/"
        )

    def test_resolve_authority_regex_preserves_path(self):
        """Test that regex correctly replaces tenant while preserving additional path segments"""
        config = AgentAuthConfiguration(
            tenant_id="12345678-1234-1234-1234-123456789abc",
            authority="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        )
        result = MsalAuth._resolve_authority(config, None)
        assert (
            result
            == "https://login.microsoftonline.com/12345678-1234-1234-1234-123456789abc/oauth2/v2.0/authorize"
        )


# class TestMsalAuthAgentic:

#     @pytest.mark.asyncio
#     async def test_get_agentic_user_token_data_flow(self, mocker):
#         agent_app_instance_id = "test-agent-app-id"
#         app_token = "app-token"
#         instance_token = "instance-token"
#         agent_user_token = "agent-token"
#         upn = "test-upn"
#         scopes = ["user.read"]

#         mocker.patch.object(MsalAuth, "get_agentic_instance_token", return_value=[instance_token, app_token])

#         mock_auth = MockMsalAuth(mocker, ConfidentialClientApplication)
#         mocker.patch.object(ConfidentialClientApplication, "__new__", return_value=mocker.Mock(spec=ConfidentialClientApplication))

#         result = await mock_auth.get_agentic_user_token(agent_app_instance_id, upn, scopes)
#         mock_auth.get_agentic_instance_token.assert_called_once_with(agent_app_instance_id)

#         assert result == agent_user_token

#     @pytest.mark.asyncio
#     async def test_get_agentic_user_token_failure(self, mocker):
#         agent_app_instance_id = "test-agent-app-id"
#         app_token = "app-token"
#         instance_token = "instance-token"
#         agent_user_token = "agent-token"
#         upn = "test-upn"
#         scopes = ["user.read"]

#         mocker.patch.object(MsalAuth, "get_agentic_instance_token", return_value=[instance_token, app_token])

#         mock_auth = MockMsalAuth(mocker, ConfidentialClientApplication, acquire_token_for_client_return=None)
#         mocker.patch.object(ConfidentialClientApplication, "__new__", return_value=mocker.Mock(spec=ConfidentialClientApplication))

#         result = await mock_auth.get_agentic_user_token(agent_app_instance_id, upn, scopes)

#         mock_auth.get_agentic_instance_token.assert_called_once_with(agent_app_instance_id)

#         assert result is None
