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

## Storage Utilities

