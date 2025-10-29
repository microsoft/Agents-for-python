# from microsoft_agents.activity import Activity

# from ..agent_client import AgentClient

# class AutoClient:
    
#     def __init__(self, agent_client: AgentClient):
#         self._agent_client = agent_client

#     async def generate_message(self) -> str:
#         pass

#     async def run(self, max_turns: int = 10, time_between_turns: float = 2.0) -> None:
        
#         for i in range(max_turns):
#             await self._agent_client.send_activity(
#                 Activity(type="message", text=self.generate_message())
#             )