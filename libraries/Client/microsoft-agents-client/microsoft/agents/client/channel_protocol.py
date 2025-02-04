from typing import Protocol

class ChannelProtocol(Protocol):
    async def post_activity(self, to_bot_id: str) -> dict:
        raise NotImplementedError()