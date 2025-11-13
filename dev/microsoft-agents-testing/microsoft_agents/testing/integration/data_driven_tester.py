import pytest

from .data_driven_test import DataDrivenTest
# from typing import Callable, TypeVar

# from .core import Integration

# async def run_data_driven_test(input_file: str) -> None:
#     """
#     Run data-driven tests based on the provided input file.
#     """
#     pass

# T = TypeVar("T", bound=Integration)

# def factory(tests_path: str = "./") -> Callable[T, T]:

#     # for file in file

#     files = []

#     def decorator(test_cls: T) -> T:

#         for file_name in files:

#             test_case_name = f"test_data_driven__{file_name}"

#             def func(self, agent_client, response_client) -> None:


#             setattr(test_cls, test_case_name, func)

#         return test_cls

#     return decorator

class DataDrivenTester:

    _test_path: str

    @pytest.mark.asyncio
    async def test_data_driven(self, agent_client, response_client) -> None:
        
        ddt = DataDrivenTest(self._test_path)

        responses = []

        await for step in ddt:
            if isinstance(step, Activity):
                await agent_client.send_activity(step)
            elif isinstance(step, dict):
                # assertion
                responses.extend(await response_client.pop())

                