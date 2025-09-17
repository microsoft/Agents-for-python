from tests._common import SDKFixtures, TestingEnvironment

class MyTestingEnv(TestingEnvironment):
    pass
    

class TestFeature(SDKFixtures[MyTestingEnv]):

    def test_something(self, activity, turn_context, user_token_client, oauth_flow, auth_handlers, connection_manager, authorization):
        assert activity is not None
        assert turn_context is not None
        assert user_token_client is not None
        assert oauth_flow is not None
        assert auth_handlers is not None
        assert connection_manager is not None
        assert authorization is not None

    def test_another_thing(self, activity):
        assert activity is not None
        assert activity.type == "message"
        assert isinstance(activity, Activity)