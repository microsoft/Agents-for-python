import pytest

from microsoft_agents.activity import (
    Activity,
    ConversationResourceResponse,
    ConversationParameters,
    DeliveryModes,
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
    ClaimsIdentity,
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "delivery_mode",
        [DeliveryModes.expect_replies, DeliveryModes.stream],
        )
    async def test_process_activity_expect_replies_and_stream_without_service_url(
        self, mocker, user_token_client, adapter, delivery_mode
    ):
        user_token_client.get_access_token = mocker.AsyncMock(
            return_value="user_token_value"
        )
        adapter.run_pipeline = mocker.AsyncMock()

        async def callback(context: TurnContext):
            return None

        activity = Activity(  # type: ignore
            type="message",
            conversation={"id": "conversation123"},
            channel_id="channel_id",
            delivery_mode=delivery_mode
        )

        claims_identity = ClaimsIdentity(
            {
                "aud": "agent_app_id",
                "ver": "2.0",
                "azp": "outgoing_app_id",
            },
            is_authenticated=True,
        )

        await adapter.process_activity(
            claims_identity,
            activity,
            callback,
        )

        adapter.run_pipeline.assert_awaited_once()

        context_arg, callback_arg = adapter.run_pipeline.call_args[0]
        assert callback_arg == callback
        assert context_arg.activity == activity

        assert context_arg.activity.conversation.id == "conversation123"
        assert context_arg.activity.channel_id == "channel_id"
        assert context_arg.activity.service_url is None
        assert context_arg.turn_state[ChannelServiceAdapter.USER_TOKEN_CLIENT_KEY] is user_token_client
        assert ChannelServiceAdapter._AGENT_CONNECTOR_CLIENT_KEY not in context_arg.turn_state

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "delivery_mode",
        [DeliveryModes.expect_replies, DeliveryModes.stream],
        )
    async def test_process_activity_expect_replies_and_stream_with_service_url(
        self, mocker, user_token_client, connector_client, adapter, delivery_mode
    ):
        user_token_client.get_access_token = mocker.AsyncMock(
            return_value="user_token_value"
        )
        adapter.run_pipeline = mocker.AsyncMock()

        async def callback(context: TurnContext):
            return None

        activity = Activity(  # type: ignore
            type="message",
            conversation={"id": "conversation123"},
            channel_id="channel_id",
            delivery_mode=delivery_mode,
            service_url="service_url",
        )

        claims_identity = ClaimsIdentity(
            {
                "aud": "agent_app_id",
                "ver": "2.0",
                "azp": "outgoing_app_id",
            },
            is_authenticated=True,
        )

        await adapter.process_activity(
            claims_identity,
            activity,
            callback,
        )

        adapter.run_pipeline.assert_awaited_once()

        context_arg, callback_arg = adapter.run_pipeline.call_args[0]
        assert callback_arg == callback
        assert context_arg.activity == activity

        assert context_arg.activity.conversation.id == "conversation123"
        assert context_arg.activity.channel_id == "channel_id"
        assert context_arg.activity.service_url == "service_url"
        assert context_arg.turn_state[ChannelServiceAdapter.USER_TOKEN_CLIENT_KEY] is user_token_client
        assert context_arg.turn_state[ChannelServiceAdapter._AGENT_CONNECTOR_CLIENT_KEY] is connector_client

    @pytest.mark.asyncio
    async def test_process_activity_normal_no_service_url(
        self, mocker, user_token_client, adapter
    ):
        user_token_client.get_access_token = mocker.AsyncMock(
            return_value="user_token_value"
        )
        adapter.run_pipeline = mocker.AsyncMock()

        async def callback(context: TurnContext):
            return None

        activity = Activity(  # type: ignore
            type="message",
            conversation={"id": "conversation123"},
            channel_id="channel_id",
        )

        claims_identity = ClaimsIdentity(
            {
                "aud": "agent_app_id",
                "ver": "2.0",
                "azp": "outgoing_app_id",
            },
            is_authenticated=True,
        )

        with pytest.raises(Exception) as exc_info:
            await adapter.process_activity(
                claims_identity,
                activity,
                callback,
            )

    @pytest.mark.asyncio
    async def test_process_proactive(self, mocker, user_token_client, connector_client, adapter):
        user_token_client.get_access_token = mocker.AsyncMock(
            return_value="user_token_value"
        )
        adapter.run_pipeline = mocker.AsyncMock()

        async def callback(context: TurnContext):
            return None

        activity = Activity(  # type: ignore
            type="message",
            conversation={"id": "conversation123"},
            channel_id="channel_id",
            service_url="service_url",
        )

        claims_identity = ClaimsIdentity(
            {
                "aud": "agent_app_id",
                "ver": "2.0",
                "azp": "outgoing_app_id",
            },
            is_authenticated=True,
        )

        await adapter.process_proactive(
            claims_identity,
            activity,
            "audience",
            callback,
        )

        adapter.run_pipeline.assert_awaited_once()

        context_arg, callback_arg = adapter.run_pipeline.call_args[0]
        assert callback_arg == callback
        assert context_arg.activity == activity

        assert context_arg.activity.conversation.id == "conversation123"
        assert context_arg.activity.channel_id == "channel_id"
        assert context_arg.activity.service_url == "service_url"
        assert context_arg.turn_state[ChannelServiceAdapter.USER_TOKEN_CLIENT_KEY] is user_token_client
        assert context_arg.turn_state[ChannelServiceAdapter._AGENT_CONNECTOR_CLIENT_KEY] is connector_client