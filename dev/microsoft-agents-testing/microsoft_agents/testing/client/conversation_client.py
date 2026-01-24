# from microsoft_agents.testing.check import Check
# from microsoft_agents.testing.underscore import _, Underscore

# class Conversation:
#     def __init__(self, agent_client: AgentClient):
#         self._client = agent_client
#         self._history: list[tuple[str, list[Activity]]] = []
    
#     async def turn(
#         self,
#         message: str,
#         expect: str | Underscore | Callable | list = None,
#         response_wait: float | None = None
#     ) -> list[Activity]:
#         """Send a message, wait for response, optionally assert.
        
#         Args:
#             message: The message to send.
#             expect: Optional assertion (string, underscore, callable, or list).
#             response_wait: Time to wait for responses. 
#                         Defaults to 1.0s if expect is set, 0.0s otherwise.
#         """
#         if response_wait is None:
#             response_wait = 1.0 if expect is not None else 0.0
        
#         responses = await self._client.send(message, response_wait=response_wait)
#         self._history.append((message, responses))
        
#         if expect is not None:
#             self._assert(responses, expect)
        
#         return responses
    
#     def _assert(self, responses: list[Activity], expect):
#         """Apply Check-style assertions to responses."""
#         check = Check(responses)
        
#         if isinstance(expect, list):
#             # Multiple conditions
#             for cond in expect:
#                 self._apply_condition(check, cond)
#         else:
#             self._apply_condition(check, expect)
    
#     def _apply_condition(self, check: Check, condition):
#         """Apply a single condition (string, underscore, or callable)."""
#         if isinstance(condition, str):
#             # String → Check.that(_.text).matches(condition)
#             check.that(_.text).matches(condition)
#         elif isinstance(condition, Underscore):
#             # Underscore expression → Check.that(condition)
#             check.that(condition)
#         elif callable(condition):
#             # Lambda → Check.where(condition)
#             check.where(condition)
#         else:
#             raise TypeError(f"Invalid expect type: {type(condition)}")
    
#     @property
#     def transcript(self) -> str:
#         """Format conversation history for debugging."""
#         lines = []
#         for user_msg, responses in self._history:
#             lines.append(f"User: {user_msg}")
#             for r in responses:
#                 lines.append(f"Agent: {r.text}")
#         return "\n".join(lines)
    
#     async def __aenter__(self):
#         return self
    
#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         if exc_type:
#             # Print transcript on failure for debugging
#             print(f"\n--- Conversation Transcript ---\n{self.transcript}\n")


# ### also want an assertion version of conversation_client.py