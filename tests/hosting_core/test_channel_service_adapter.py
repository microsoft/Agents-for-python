import pytest

from microsoft_agents.activity import (
    ConversationResourceResponse,
    ConversationParameters
)
from microsoft_agents.hosting.core import (
    ChannelServiceAdapter,
    TurnContext,
    ConnectorClientBase,
    UserTokenClientBase,
    ChannelServiceClientFactoryBase,
    ConversationsBase,
    TeamsConnectorClient,
    UserTokenClient,
)

class MyChannelServiceAdapter(ChannelServiceAdapter):
    pass

class TestChannelServiceAdapter:

    @pytest.fixture
    def connector_client(self, mocker):
        connector_client = mocker.Mock(spec=TeamsConnectorClient)
        mocker.patch.object(TeamsConnectorClient, "__new__", return_value=connector_client)
        return connector_client
    
    @pytest.fixture
    def user_token_client(self, mocker):
        user_token_client = mocker.Mock(spec=UserTokenClient)
        mocker.patch.object(UserTokenClient, "__new__", return_value=user_token_client)
        return user_token_client

    @pytest.fixture
    def client_factory(self, mocker, connector_client, user_token_client):
        factory = RestChannelServiceClientFactory(
            mocker.Mock(spec=Connections),
            token_service_endpoint,
            token_service_audience
        )

    @pytest.fixture
    def adapter(self, client_factory):
        return MyChannelServiceAdapter(client_factory)


    @pytest.mark.asyncio
    async def test_create_conversation_basic(self, mocker, connector_client, factory, adapter):


# context = mocker.Mock(spec=TurnContext)
#         context.activity = activity
#         claims_identity = mocker.Mock(spec=ClaimsIdentity)
#         scopes = ["scope1"]
#         audience = "https://service.audience/"
        adapter.run_pipeline = mocker.AsyncMock()
        
        connector_client.conversations = mocker.Mock(spec=ConversationsBase)
        connector_client.conversations.create_conversation.return_value = ConversationResourceResponse(
            activity_id="activity123",
            service_url="https://service.url",
            id="conversation123"
        )

        async def callback(context: TurnContext):
            return None

        res = await adapter.create_conversation(
            "agent_app_id",
            "channel_id",
            "service_url",
            "audience",
            ConversationParameters(),
            callback
        )

        assert factory.create_connector_client.call_count == 1
        assert factory.create_user_token_client.call_count == 1

        assert adapter.run_pipeline.called