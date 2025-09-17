from .testing_environment import TestingEnvironment

class DefaultTestingEnvironment(TestingEnvironment):

    def __init__(self, load_defaults=TEST_DEFAULTS):
        self.DEFAULTS = load_defaults()

    ### Activity Handling

    def mock_activity(self, mocker) -> None:
        pass

    def Activity(self, mocker, *args, **kwargs) -> Activity:
        return Activity(self._DEFAULTS.activity)
    
    def mock_turn_context(self, mocker) -> None:
        pass

    def TurnContext(self, mocker, *args, **kwargs) -> TurnContext:
        return TurnContext(self._DEFAULTS.turn_context)
    
    ### Auth
    
    def mock_user_token_client(self, mocker) -> None:
        pass

    def UserTokenClient(self, mocker, *args, **kwargs) -> UserTokenClient:
        return UserTokenClient(self._DEFAULTS.user_token_client)
    
    def AuthHandler(self, mocker, *args, **kwargs) -> AuthHandler:
        return AuthHandler(self._DEFAULTS.auth_handler)
    
    def mock_connection_manager(self, mocker) -> None:
        pass

    def ConnectionManager(self, mocker, *args, **kwargs) -> ConnectionManager:
        return ConnectionManager(self._DEFAULTS.connection_manager)
    
    def mock_authorization(self, mocker) -> None:
        pass

    def Authorization(self, mocker, *args, **kwargs) -> Authorization:
        return Authorization(self._DEFAULTS.authorization)