from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration

# used by MsalAuth tests
class MockMsalAuth(MsalAuth):
    """
    Mock object for MsalAuth
    """

    def __init__(self, mocker, client_type, acquire_token_for_client_return={"access_token": "token"}):
        super().__init__(AgentAuthConfiguration())
        mock_client = mocker.Mock(spec=client_type)

        mock_client.acquire_token_for_client = mocker.Mock(
            return_value=acquire_token_for_client_return
        )
        mock_client.acquire_token_on_behalf_of = mocker.Mock(
            return_value={"access_token": "token"}
        )
        self.mock_client = mock_client

        self._create_client_application = mocker.Mock(return_value=self.mock_client)

def agentic_mock_class_MsalAuth(
    mocker,
    get_agentic_application_token_return=None,
    get_agentic_instance_token_return=None,
    get_agentic_user_token_return=None,
):
    mocker.patch.object(MsalAuth, "get_agentic_application_token", return_value=get_agentic_application_token_return)
    mocker.patch.object(MsalAuth, "get_agentic_instance_token", return_value=get_agentic_instance_token_return)
    mocker.patch.object(MsalAuth, "get_agentic_user_token", return_value=get_agentic_user_token_return)