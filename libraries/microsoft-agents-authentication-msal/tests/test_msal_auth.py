import unittest
from unittest.mock import Mock
import pytest
from msal import ManagedIdentityClient, ConfidentialClientApplication
from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration


class TestingMsalAuth(MsalAuth):
    """
    Mock object for MsalAuth
    """

    def __init__(self, client_type):
        super().__init__(AgentAuthConfiguration())
        mock_client = Mock(spec=client_type)

        mock_client.acquire_token_for_client = Mock(
            return_value={"access_token": "token"}
        )
        mock_client.acquire_token_on_behalf_of = Mock(
            return_value={"access_token": "token"}
        )
        self.mock_client = mock_client

        self._create_client_application = Mock(return_value=self.mock_client)


class TestMsalAuth:
    """
    Test suite for testing MsalAuth functionality
    """

    @pytest.mark.asyncio
    async def test_get_access_token_managed_identity(self):
        mock_auth = TestingMsalAuth(ManagedIdentityClient)
        token = await mock_auth.get_access_token(
            "https://test.api.botframework.com", scopes=["test-scope"]
        )

        assert token == "token"
        mock_auth.mock_client.acquire_token_for_client.assert_called_with(
            resource="https://test.api.botframework.com"
        )

    @pytest.mark.asyncio
    async def test_get_access_token_confidential(self):
        mock_auth = TestingMsalAuth(ConfidentialClientApplication)
        token = await mock_auth.get_access_token(
            "https://test.api.botframework.com", scopes=["test-scope"]
        )

        assert token == "token"
        mock_auth.mock_client.acquire_token_for_client.assert_called_with(
            scopes=["test-scope"]
        )

    @pytest.mark.asyncio
    async def test_aquire_token_on_behalf_of_managed_identity(self):
        mock_auth = TestingMsalAuth(ManagedIdentityClient)

        try:
            await mock_auth.aquire_token_on_behalf_of(
                scopes=["test-scope"], user_assertion="test-assertion"
            )
        except NotImplementedError:
            assert True
        else:
            assert False

    @pytest.mark.asyncio
    async def test_aquire_token_on_behalf_of_confidential(self):
        mock_auth = TestingMsalAuth(ConfidentialClientApplication)
        mock_auth._create_client_application = Mock(return_value=mock_auth.mock_client)

        token = await mock_auth.aquire_token_on_behalf_of(
            scopes=["test-scope"], user_assertion="test-assertion"
        )

        assert token == "token"
        mock_auth.mock_client.acquire_token_on_behalf_of.assert_called_with(
            scopes=["test-scope"], user_assertion="test-assertion"
        )
