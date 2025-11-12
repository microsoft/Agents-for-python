# import json
# import asyncio

# from microsoft_agents.activity import Activity
# from microsoft_agents.testing.core import (
#     AgentClient,
#     ResponseClient
# )

# from microsoft_agents.testing.asserts import check_activity

# class DataDrivenTestModule:

#     def __init__(
#         self,
#         test_file_path: str,
#         agent_client: AgentClient,
#         response_client: ResponseClient
#     ) -> None:
        
#         data = json.load(open(test_file_path, "r"))

#         self._agent_client = agent_client
#         self._response_client = response_client

#         self._input_activities: list[Activity] = []
#         self._activity_assertions: list[dict] = []

#     async def assert(self) -> bool:

#         for input_activity in self._input_activities:
#             await self._agent_client.send_activity(input_activity)

#         await asyncio.sleep(1)

#         for activity_assertion in self._activity_assertions:
#             # select first
#             selected_activity = None
#             check_activity(selected_activity, activity_assertion)