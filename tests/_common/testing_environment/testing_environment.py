from re import A
from microsoft_agents.activity import (
    Activity
)
from microsoft_agents.hosting.core import (
    TurnContext,
    UserTokenClient,
    OAuthFlow,
    AuthHandler,
    ConnectionManager,
    Authorization,
)

from tests._common.data.defaults import TEST_DEFAULTS

class TestingEnvironment:

    ### Activity Handling

    def mock_activity(self, mocker) -> None:
        pass

    def Activity(self, mocker, *args, **kwargs) -> Activity:
        raise NotImplementedError()
    
    def mock_turn_context(self, mocker) -> None:
        pass

    def TurnContext(self, mocker, *args, **kwargs) -> TurnContext:
        raise NotImplementedError()
    
    ### Auth
    
    def mock_user_token_client(self, mocker) -> None:
        pass

    def UserTokenClient(self, mocker, *args, **kwargs) -> UserTokenClient:
        raise NotImplementedError()
    
    def AuthHandler(self, mocker, *args, **kwargs) -> AuthHandler:
        raise NotImplementedError
    
    def mock_connection_manager(self, mocker) -> None:
        pass

    def ConnectionManager(self, mocker, *args, **kwargs) -> ConnectionManager:
        raise NotImplementedError()
    
    def mock_authorization(self, mocker) -> None:
        pass

    def Authorization(self, mocker, *args, **kwargs) -> Authorization:
        raise NotImplementedError()