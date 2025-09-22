from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration


class MockMsalAuth(MsalAuth):
    """
    Mock object for MsalAuth
    """

    def __init__(self, mocker, client_type):
        super().__init__(AgentAuthConfiguration())
        mock_client = mocker.Mock(spec=client_type)

        mock_client.acquire_token_for_client = mocker.Mock(
            return_value={"access_token": "token"}
        )
        mock_client.acquire_token_on_behalf_of = mocker.Mock(
            return_value={"access_token": "token"}
        )
        self.mock_client = mock_client

        self._create_client_application = mocker.Mock(return_value=self.mock_client)
