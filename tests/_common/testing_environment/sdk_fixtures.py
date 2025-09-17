from typing import Generic, TypeVar

import pytest

from .testing_environment import TestingEnvironment
from .default_testing_environment import DefaultTestingEnvironment

TestingEnvironmentT = TypeVar("T", bound=TestingEnvironment)

class SDKFixtures(Generic[TestingEnvironmentT]):

    def setup(self):
        self.env = TestingEnvironmentT()

    @pytest.fixture
    def activity(self, mocker):
        self.env.mock_activity(mocker)
        return self.env.Activity(mocker)
    
    @pytest.fixture
    def turn_context(self, mocker):
        self.env.mock_turn_context(mocker)
        return self.env.TurnContext(mocker)

    @pytest.fixture
    def user_token_client(self, mocker):
        self.env.mock_user_token_client(mocker)
        return self.env.UserTokenClient(mocker)
    
    @pytest.fixture
    def oauth_flow(self, mocker):
        self.env.mock_oauth_flow(mocker)
        return self.env.OAuthFlow(mocker)
    
    @pytest.fixture
    def auth_handlers(self, mocker):
        return self.env.AuthHandler(mocker)
    
    @pytest.fixture
    def connection_manager(self, mocker):
        self.env.mock_connection_manager(mocker)
        return self.env.ConnectionManager(mocker)
    
    @pytest.fixture
    def authorization(self, mocker):
        self.env.mock_authorization(mocker)
        return self.env.Authorization(mocker)