import unittest
from unittest.mock import Mock
import pytest
from msal import ManagedIdentityClient, ConfidentialClientApplication
from microsoft.agents.authentication.msal import MsalAuth
from microsoft.agents.hosting.core.authorization import AgentAuthConfiguration

class TestMsalAuth:
    """
    Test suite for testing MsalAuth functionality
    """
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.mock_client = Mock()
        self.mock_client.acquire_token_for_client.return_value = {"access_token": "token"}
        self.mock_client.acquire_token_on_behalf_of.return_value = {"access_token": "token"}
        self.auth = MsalAuth(AgentAuthConfiguration()) 
        self.auth._create_client_application = Mock(return_value=self.mock_client)

    @pytest.mark.asyncio
    async def test_get_access_token_managed_identity(self):
        self.mock_client.mock_add_spec(ManagedIdentityClient)
        token = await self.auth.get_access_token("https://test.api.botframework.com", scopes=["test-scope"])

        assert token == "token"
        self.mock_client.acquire_token_for_client.assert_called_with(resource="https://test.api.botframework.com")

    @pytest.mark.asyncio
    async def test_get_access_token_confidential(self):
        self.mock_client.mock_add_spec(ConfidentialClientApplication)
        token = await self.auth.get_access_token("https://test.api.botframework.com", scopes=["test-scope"])

        assert token == "token"
        self.mock_client.acquire_token_for_client.assert_called_with(scopes=["test-scope"])

    @pytest.mark.asyncio
    async def test_aquire_token_on_behalf_of_managed_identity(self):
        self.mock_client.mock_add_spec(ManagedIdentityClient)

        try:
            await self.auth.aquire_token_on_behalf_of(scopes=["test-scope"], user_assertion="test-assertion")
        except NotImplementedError:
            assert True
        else:
            assert False


    @pytest.mark.asyncio
    async def test_aquire_token_on_behalf_of_confidential(self):
        self.mock_client.mock_add_spec(ConfidentialClientApplication)
        self.auth._create_client_application = Mock(return_value=self.mock_client)

        token = await self.auth.aquire_token_on_behalf_of(scopes=["test-scope"], user_assertion="test-assertion")

        assert token == "token"
        self.mock_client.acquire_token_on_behalf_of.assert_called_with(scopes=["test-scope"], user_assertion="test-assertion")