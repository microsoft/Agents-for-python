from typing import Generic, TypeVar

import pytest

from .testing_environment import TestingEnvironment
from .default_testing_environment import DefaultTestingEnvironment

TestingEnvironmentT = TypeVar("T", bound=TestingEnvironment)

class SDKFixtures(Generic[TestingEnvironmentT]):

    def __init__(self):
        self.testenv: TestingEnvironmentT

    def setup_method(self):
        self.testenv = TestingEnvironmentT()

    @pytest.fixture
    def activity(self, mocker):
        return self.testenv.Activity(mocker)
    
    @pytest.fixture
    def turn_context(self, mocker):
        return self.testenv.TurnContext(mocker)

    @pytest.fixture
    def user_token_client(self, mocker):
        return self.testenv.UserTokenClient(mocker)
    
    @pytest.fixture
    def oauth_flow(self, mocker):
        return self.testenv.OAuthFlow(mocker)
    
    @pytest.fixture
    def auth_handlers(self, mocker):
        return self.testenv.AuthHandler(mocker)
    
    @pytest.fixture
    def connection_manager(self, mocker):
        return self.testenv.ConnectionManager(mocker)
    
    @pytest.fixture
    def authorization(self, mocker, storage, connection_manager, auth_handlers):
        return self.testenv.Authorization(mocker, storage, connection_manager, auth_handlers)
    
    @pytest.fixture
    def testenv(self):
        return self.testenv