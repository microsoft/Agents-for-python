# Agents SDK for Python Testing

This document serves as a guide to the utilities we provide internally to test this SDK. If you extend the testing features of this codebase, please document it here for future devs (or yourself even).

## Directory Structure


### Module Names

This directory follows the same structure as the package structure. If there is a test module that tests the functionality of a module in the packages source code, then please use the format `test_{ORIGINAL_MODULE}.py` file naming convention. If a module is an extra module that only exists in testing and has no counterpart in the packages source code, then it is encouraged that you prefix it with an underscore. The only exception is if a parent (or ancestor) directory of the testing Python file already has an underscore prefix. For example:

```
microsoft_agents/hosting/core
    __init__.py

    _common/
        __init__.py
        bar.py

    app/
        __init__.py
        _helper.py
        test_agent_application.py

    _foo.py
    test_turn_context.py
    test_utils.py

```

### `tests/_common`

## Mocking and Testing Environments

### Usage and Philosophy

I am open to other approaches, but I'll describe my approach here with an example:

```python

DEFAULTS = TEST_DEFAULTS()

class OAuthFlowTestEnvBase(DefaultTestingEnvironment, TestingUserTokenClientMixin, TestingActivityMixin):
    ...

class OAuthFlowTestEnv(OAuthFlowTestEnvBase):

    def mock_TokenExchangeState(self, mocker, get_encoded_value_return):
        mocker.patch.object(
            TokenExchangeState, "get_encoded_state", return_value=get_encoded_value_return
        )

    @pytest.fixture(params=FLOW_STATES.ALL())
    def sample_flow_state(self, request):
        return request.param.model_copy()

# more code

class TestOauthFlow(OauthFlowTestEnv):

    @pytest.mark.asyncio
    async def test_get_user_token_failure(self, testenv, mocker, sample_flow_state):
        # setup
        user_token_client = testenv.UserTokenClient(mocker, get_token_return=None)
        flow = OAuthFlow(sample_flow_state, user_token_client)
        expected_final_flow_state = flow.flow_state

        # test
        token_response = await flow.get_user_token()

        # verify
        assert token_response == TokenResponse()
        assert flow.flow_state == expected_final_flow_state
        user_token_client.user_token.get_token.assert_called_once_with(
            user_id=DEFAULTS.user_id,
            connection_name=DEFAULTS.abs_oauth_connection_name,
            channel_id=DEFAULTS.channel_id,
            code=None,
        )
```

This is a test case for the OAuthFlow class.

## Storage Utilities


