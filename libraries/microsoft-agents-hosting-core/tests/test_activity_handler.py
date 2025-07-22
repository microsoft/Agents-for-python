import pytest
from unittest.mock import AsyncMock
from microsoft.agents.hosting.core import ActivityHandler, TurnContext
from microsoft.agents.activity import (
    ActivityTypes,
    ChannelAccount,
    MessageReaction,
    SignInConstants,
    InvokeResponse,
)


class TestActivityHandler:
    @pytest.fixture
    def handler(self):
        return ActivityHandler()

    @pytest.fixture
    def turn_context(self):
        return AsyncMock(spec=TurnContext)

    @pytest.mark.asyncio
    async def test_on_turn_message_activity(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.type = ActivityTypes.message
        handler.on_message_activity = AsyncMock()
        await handler.on_turn(turn_context)
        handler.on_message_activity.assert_called_once_with(turn_context)

    @pytest.mark.asyncio
    async def test_on_turn_conversation_update_activity(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.type = ActivityTypes.conversation_update
        handler.on_conversation_update_activity = AsyncMock()
        await handler.on_turn(turn_context)
        handler.on_conversation_update_activity.assert_called_once_with(turn_context)

    @pytest.mark.asyncio
    async def test_on_turn_event_activity(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.type = ActivityTypes.event
        handler.on_event_activity = AsyncMock()
        await handler.on_turn(turn_context)
        handler.on_event_activity.assert_called_once_with(turn_context)

    @pytest.mark.asyncio
    async def test_on_turn_unrecognized_activity_type(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.type = "unknown"
        handler.on_unrecognized_activity_type = AsyncMock()
        await handler.on_turn(turn_context)
        handler.on_unrecognized_activity_type.assert_called_once_with(turn_context)

    @pytest.mark.asyncio
    async def test_on_message_activity(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        await handler.on_message_activity(turn_context)
        # No exception means the test passed

    @pytest.mark.asyncio
    async def test_on_conversation_update_activity_members_added(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.members_added = [ChannelAccount(id="user1")]
        handler.on_members_added_activity = AsyncMock()
        await handler.on_conversation_update_activity(turn_context)
        handler.on_members_added_activity.assert_called_once_with(
            turn_context.activity.members_added, turn_context
        )

    @pytest.mark.asyncio
    async def test_on_conversation_update_activity_members_removed(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.members_removed = [ChannelAccount(id="user1")]
        handler.on_members_removed_activity = AsyncMock()
        await handler.on_conversation_update_activity(turn_context)
        handler.on_members_removed_activity.assert_called_once_with(
            turn_context.activity.members_removed, turn_context
        )

    @pytest.mark.asyncio
    async def test_on_message_reaction_activity_reactions_added(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.reactions_added = [MessageReaction(type="like")]
        handler.on_reactions_added = AsyncMock()
        await handler.on_message_reaction_activity(turn_context)
        handler.on_reactions_added.assert_called_once_with(
            turn_context.activity.reactions_added, turn_context
        )

    @pytest.mark.asyncio
    async def test_on_message_reaction_activity_reactions_removed(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.reactions_removed = [MessageReaction(type="like")]
        handler.on_reactions_removed = AsyncMock()
        await handler.on_message_reaction_activity(turn_context)
        handler.on_reactions_removed.assert_called_once_with(
            turn_context.activity.reactions_removed, turn_context
        )

    @pytest.mark.asyncio
    async def test_on_event_activity_token_response(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.name = SignInConstants.token_response_event_name
        handler.on_token_response_event = AsyncMock()
        await handler.on_event_activity(turn_context)
        handler.on_token_response_event.assert_called_once_with(turn_context)

    @pytest.mark.asyncio
    async def test_on_event_activity_other_event(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.name = "other_event"
        handler.on_event = AsyncMock()
        await handler.on_event_activity(turn_context)
        handler.on_event.assert_called_once_with(turn_context)

    @pytest.mark.asyncio
    async def test_on_invoke_activity_sign_in(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.name = SignInConstants.verify_state_operation_name
        handler.on_sign_in_invoke = AsyncMock()
        response = await handler.on_invoke_activity(turn_context)
        handler.on_sign_in_invoke.assert_called_once_with(turn_context)
        assert isinstance(response, InvokeResponse)

    @pytest.mark.asyncio
    async def test_on_invoke_activity_adaptive_card(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.name = "adaptiveCard/action"
        turn_context.activity.value = {"action": {"type": "Action.Execute"}}
        handler.on_adaptive_card_invoke = AsyncMock(return_value=None)
        response = await handler.on_invoke_activity(turn_context)
        handler.on_adaptive_card_invoke.assert_called_once()
        assert isinstance(response, InvokeResponse)

    @pytest.mark.asyncio
    async def test_on_invoke_activity_not_implemented(
        self, handler: ActivityHandler, turn_context: TurnContext
    ):
        turn_context.activity.name = "unknown"
        response = await handler.on_invoke_activity(turn_context)

        assert response.status == 501
