import pytest

from microsoft_agents.activity import (
    ConversationResourceResponse,
    ConversationParameters,
)
from microsoft_agents.hosting.core import (
    ChannelServiceAdapter,
    TurnContext,
    ConnectorClientBase,
    UserTokenClientBase,
    ChannelServiceClientFactoryBase,
    RestChannelServiceClientFactory,
    TeamsConnectorClient,
    UserTokenClient,
    Connections,
)

from microsoft_agents.hosting.core.connector.conversations_base import ConversationsBase


class MyChannelServiceAdapter(ChannelServiceAdapter):
    pass


class TestChannelServiceAdapter:

    @pytest.fixture
    def connector_client(self, mocker):
        connector_client = mocker.Mock(spec=TeamsConnectorClient)
        mocker.patch.object(
            TeamsConnectorClient, "__new__", return_value=connector_client
        )
        return connector_client

    @pytest.fixture
    def user_token_client(self, mocker):
        user_token_client = mocker.Mock(spec=UserTokenClient)
        mocker.patch.object(UserTokenClient, "__new__", return_value=user_token_client)
        return user_token_client

    @pytest.fixture
    def connection_manager(self, mocker, user_token_client):
        connection_manager = mocker.Mock(spec=Connections)
        connection_manager.get_token_provider = mocker.Mock(
            return_value=user_token_client
        )
        return connection_manager

    @pytest.fixture
    def factory(self, connection_manager):
        client_factory = RestChannelServiceClientFactory(connection_manager)
        return client_factory

    @pytest.fixture
    def adapter(self, factory):
        return MyChannelServiceAdapter(factory)

    @pytest.mark.asyncio
    async def test_create_conversation_basic(
        self, mocker, user_token_client, connector_client, adapter
    ):

        user_token_client.get_access_token = mocker.AsyncMock(
            return_value="user_token_value"
        )
        adapter.run_pipeline = mocker.AsyncMock()

        connector_client.conversations = mocker.Mock(spec=ConversationsBase)
        connector_client.conversations.create_conversation.return_value = (
            ConversationResourceResponse(
                activity_id="activity123",
                service_url="https://service.url",
                id="conversation123",
            )
        )

        async def callback(context: TurnContext):
            return None

        await adapter.create_conversation(
            "agent_app_id",
            "channel_id",
            "service_url",
            "audience",
            ConversationParameters(),
            callback,
        )

        adapter.run_pipeline.assert_awaited_once()

        context_arg, callback_arg = adapter.run_pipeline.call_args[0]
        assert callback_arg == callback
        assert context_arg.activity.conversation.id == "conversation123"
        assert context_arg.activity.channel_id == "channel_id"
        assert context_arg.activity.service_url == "service_url"
