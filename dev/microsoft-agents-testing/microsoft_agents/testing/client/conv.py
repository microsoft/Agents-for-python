# from __future__ import annotations
# from typing import Callable
# from microsoft_agents.activity import Activity
# from microsoft_agents.testing.check import Check
# from microsoft_agents.testing.underscore import _, Underscore

# from .agent_client import AgentClient

# class Conversation:
#     """High-level conversational interface for agent testing."""
    
#     def __init__(self, client: AgentClient) -> None:
#         self._client = client
#         self._turns: list[Turn] = []
    
#     async def say(
#         self,
#         message: str,
#         *,
#         expect: str | Underscore | Callable | None = None,
#         wait: float | None = None,
#     ) -> list[Activity]:
#         """Send a message and optionally assert on response."""
#         # Default wait: 1.0s if expecting, 0.0s otherwise
#         if wait is None:
#             wait = 1.0 if expect is not None else 0.0
        
#         responses = await self._client.send(message, wait=wait)
#         self._turns.append(Turn(message, responses))
        
#         if expect is not None:
#             self._assert(responses, expect)
        
#         return responses
    
#     def _assert(self, responses: list[Activity], expect) -> None:
#         check = Check(responses)
#         if isinstance(expect, str):
#             check.that(_.text).matches(expect)
#         elif isinstance(expect, Underscore):
#             check.that(expect).is_truthy()
#         elif callable(expect):
#             expect(check)
    
#     @property
#     def history(self) -> list[Turn]:
#         return list(self._turns)

# @dataclass
# class Turn:
#     """A single turn in a conversation."""
#     user_message: str
#     agent_responses: list[Activity]