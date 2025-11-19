# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable, TypeVar

import pytest

from microsoft_agents.testing.integration.core import Integration

from .data_driven_test import DataDrivenTest
from .load_ddts import load_ddts

IntegrationT = TypeVar("IntegrationT", bound=type[Integration])

def _add_test_method(test_cls: type[Integration], data_driven_test: DataDrivenTest) -> None:
    """Add a test method to the test class for the given data driven test.

    :param test_cls: The test class to add the test method to.
    :param data_driven_test: The data driven test to add as a method.
    """

    test_case_name = (
        f"test_data_driven__{data_driven_test.name.replace('/', '_').replace('.', '_')}"
    )

    @pytest.mark.asyncio
    async def _func(self, agent_client, response_client) -> None:
        await data_driven_test.run(agent_client, response_client)

    setattr(test_cls, test_case_name, _func)


def ddt(test_path: str, recursive: bool = True) -> Callable[[IntegrationT], IntegrationT]:
    """Decorator to add data driven tests to an integration test class.

    :param test_path: The path to the data driven test files.
    :param recursive: Whether to load data driven tests recursively from subdirectories.
    :return: The decorated test class.
    """

    ddts = load_ddts(test_path, recursive=recursive)

    def decorator(test_cls: IntegrationT) -> IntegrationT:
        for data_driven_test in ddts:
            # scope data_driven_test to avoid late binding in loop
            _add_test_method(test_cls, data_driven_test)
        return test_cls

    return decorator
