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

### Mocking

When using a class or function that takes a `mocker` argument, it is highly recommended that you pass in the Pytest fixture obtained either in:

a test

```python
    def test_thing(self, some_fixture, mocker):
        mock_UserTokenClient(mocker)
```

the setup method of a class

```python
class TestThing:

    def setup_method(self, mocker):
        self.msal_auth = MockMsalAuth(mocker)
```

or in another fixture

```python
    @pytest.fixture
    def user_token_client(self, mocker):
        return mock_OAuthFlow(mocker, get_user_token_return="token")
```

### `tests/_common`


### `tests/_common/data`

Here, we encourage defining the data within the constructors of a class. I guess this helps clean up imports, but the primary purpose is to prevent tests from mutating these testing constants and interfering with other tests. The `test_defaults.py` module defines defaults for fundamental variables such as `user_id` and `channel_id`. These defaults are used in tests as well as other data constructors in `tests/_common/data`. For instance `test_flow_data.py` builds on those defaults to define FlowState objects for testing, and then `tests/_common/storage_data` builds even further on that.

### `tests/_common/storage`

Storage related functionality. This was the first shared testing utility module, so this can eventually be reorganized into the rest of the `tests/_common` structure.

### `tests/_common_fixtures`

This directory holds common fixtures that might be useful. For instance, `FlowStateFixtures` provides fixtures that are useful for testing both the OAuthFlow and Authorization classes, and it relies on `tests/_common/data/test_flow_data.py` module.

### `tests/_common/testing_objects`

This directory contains implementations and functions to construct objects that implement/extend core Protocols or mock existing functionality. In this repo, `testing_{class_name}.py` modules contain simple implementations with predictable behavior while `mock_{class_name}.py` usually contain `mock_{class_name}` and `mock_class_{class_name}` functions that wrap existing instances/classes with Pytest's mocking capabilities.

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


