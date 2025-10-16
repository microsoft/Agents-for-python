import pytest
from msal import ManagedIdentityClient, ConfidentialClientApplication

from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.core import Connections

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
