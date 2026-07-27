# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# from __future__ import annotations

# from .test_adapter import TestAdapter

# from .type_def import AgentCallbackHandler, T

# class TestFlow:
#     """Fluent helper for driving a ``TestAdapter`` conversation in tests.

#     A test flow keeps the adapter and turn callback together so tests can send
#     user activities, then inspect replies captured by the adapter's in-memory
#     queue. It is a test harness convenience, not a real channel conversation.
#     """

#     def __init__(self, adapter: TestAdapter, callback: AgentCallbackHandler):
#         """Create a flow for an adapter and agent turn callback."""

#         self._adapter = adapter
#         self._callback = callback

#     async def send(self, user_input: str) -> TestFlow:

#         return TestFlow(

#         )
