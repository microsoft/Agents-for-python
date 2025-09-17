from .mock_user_token_client import mock_UserTokenClient

class TestingUserTokenClientMixin:
    def UserTokenClient(self, mocker, *args, **kwargs):
        return mock_UserTokenClient(mocker, *args, **kwargs)