import pytest

from microsoft_agents.hosting.core import (
    ChannelServiceAdapter,
    TurnContext,
    ConnectorClientBase,
    ChannelServiceClientFactoryBase
)

class TestChannelServiceAdapter:

    @pytest.fixture
    def connector_client(self, mocker):
        return mocker.Mock(spec=ConnectorClientBase)


    @pytest.fixture
    def context(self, mocker, connector_client):
        turn_context = mocker.Mock(spec=TurnContext)
        turn_context.turn_state = {
            ChannelServiceAdapter._AGENT_CONNECTOR_CLIENT_KEY: connector_client
        }

    @pytest.fixture
    def factory(self, mocker, connector_client, user_token_client):
        factory = mocker.Mock(spec=ChannelServiceClientFactoryBase)
        factory.create_connector_client.return_value = connector_client
        factory.create_user_token_client.return_value = user_token_client
        return factory

    @pytest.fixture
    def adapter(self, factory):
        return ChannelServiceAdapter(factory)
    
    @pytest.mark.asyncio
    async def test_send_activities(self, adapter, context):

        await adapter.send_activities(context, activities=[])
