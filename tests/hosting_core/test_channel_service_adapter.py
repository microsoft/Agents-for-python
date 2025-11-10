import pytest

from microsoft_agents.hosting.core import (
    ChannelServiceAdapter,
    TurnContext,
    ConnectorClientBase,
    ChannelServiceClientFactoryBase
)

class TestChannelServiceAdapter:

    @pytest.mark.asyncio
    async def test_create_conversation(self, mocker):
        
        