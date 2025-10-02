# Agents SDK for Python Testing

This document serves as a quick guide to the utilities we provide internally to test this SDK. More information will come with work on integration testing.

## Storage Tests

More info soon. For now, there are flags defined in the code that dictate whether the Cosmos DB and the Blob storage tests are run, as these tests rely on local emulators.

## Mocking

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

This ensures Pytest will correctly manage the lifetime of your mocking logic to occur within the score of the individual test or class.

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

This directory contains common utilities for testing.

### `tests/_common/_tests`

Tests for testing utilities.

### `tests/_common/data`

Here, we encourage defining the data within the constructors of a class. I guess this helps clean up imports, but the primary purpose is to prevent tests from mutating these testing constants and interfering with other tests. The `test_defaults.py` module defines defaults for fundamental variables such as `user_id` and `channel_id`. These defaults are used in tests as well as other data constructors in `tests/_common/data`. For instance `test_flow_data.py` builds on those defaults to define FlowState objects for testing, and then `tests/_common/storage_data` builds even further on that.

### `tests/_common/storage`

Storage related functionality. This was the first shared testing utility module, so this can eventually be reorganized into the rest of the `tests/_common` structure.

### `tests/_common/fixtures`

This directory holds common fixtures that might be useful. For instance, `FlowStateFixtures` provides fixtures that are useful for testing both the OAuthFlow and Authorization classes, and it relies on `tests/_common/data/test_flow_data.py` module.

### `tests/_common/testing_objects`

This directory contains implementations and functions to construct objects that implement/extend core Protocols or mock existing functionality. In this repo, `testing_{class_name}.py` modules contain simple implementations with predictable behavior while `mock_{class_name}.py` usually contain `mock_{class_name}` and `mock_class_{class_name}` functions that wrap existing instances/classes with Pytest's mocking capabilities.

### `tests/_integration`

At the moment, there is no actual real integration testing, but there is a foundation that lets you define an environmental setup and then run a "sample" on that environment.