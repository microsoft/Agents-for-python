# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# from typing import Callable

# import pytest

# from microsoft_agents.testing.integration.core import Integration

# from .data_driven_test import DataDrivenTest

# def _add_test_method(test_cls: Integration, test_path: str, base_dir: str) -> None:

#     test_case_name = f"test_data_driven__{test_path.replace('/', '_').replace('.', '_')}"

#     @pytest.mark.asyncio
#     async def _func(self, agent_client, response_client) -> None:
#         ddt = DataDrivenTest(f"{base_dir}/{test_path}")
#         await ddt.run(agent_client, response_client)

#     setattr(test_cls, test_case_name, func)

# def ddt(test_path: str) -> Callable[[Integration], Integration]:

#     def decorator(test_cls: Integration) -> Integration:

#         test_case_name = f"test_data_driven__{test_path.replace('/', '_').replace('.', '_')}"

#         async def func(self, agent_client, response_client) -> None:
#             ddt = DataDrivenTest(test_path)

#             responses = []

#             await for step in ddt:
#                 if isinstance(step, Activity):
#                     await agent_client.send_activity(step)
#                 elif isinstance(step, dict):
#                     # assertion
#                     responses.extend(await response_client.pop())

#     return decorator
