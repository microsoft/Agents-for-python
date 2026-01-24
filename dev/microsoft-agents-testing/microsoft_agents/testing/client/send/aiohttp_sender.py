from aiohttp import ClientSession


from microsoft_agents.activity import Activity

from .sender import Sender
from ..models import SRNode


class AiohttpSender(Sender):
    
    def __init__(self, session: ClientSession):
        self._session = session

    async def send(self, activity: Activity) -> SRNode:
        
        try:
            async with self._session.post(
                "api/messages",
                json=activity.model_dump(
                    by_alias=True, exclude_unset=True, exclude_none=True, mode="json"
                )
            ) as response:
                return await SRNode.from_request(activity, response)
        
        except Exception as e:
            return await SRNode.from_request(activity, e)