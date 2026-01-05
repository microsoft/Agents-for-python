import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    DeliveryModes,
    Entity,
)

from microsoft_agents.testing import update_with_defaults

from .test_basic_agent import TestBasicAgent

class TestBasicAgentDirectLine(TestBasicAgent):
    """Test DirectLine channel for basic agent."""

    OUTGOING_PARENT = {
        "channel_id": "directline",
        "locale": "en-US",
        "conversation": {"id": "conv1"},
        "from": {"id": "user1", "name": "User"},
        "recipient": {"id": "bot", "name": "Bot"},
    }

    def populate(self, input_data: dict | None = None, **kwargs) -> Activity:
        """Helper to create Activity with defaults applied."""
        if not input_data:
            input_data = {}
        input_data.update(kwargs)
        update_with_defaults(input_data, self.OUTGOING_PARENT)
        return Activity.model_validate(input_data)

    @pytest.mark.asyncio
    async def test__send_activity__conversation_update__returns_welcome_message(
        self, agent_client, response_client
    ):
        """Test that ConversationUpdate activity returns welcome message."""
        activity = self.populate(
            type=ActivityTypes.conversation_update,
            id="activity-conv-update-001",
            timestamp="2025-07-30T23:01:11.000Z",
            from_property=ChannelAccount(id="user1"),
            recipient=ChannelAccount(id="basic-agent", name="basic-agent"),
            members_added=[
                ChannelAccount(id="basic-agent", name="basic-agent"),
                ChannelAccount(id="user1"),
            ],
            local_timestamp="2025-07-30T15:59:55.000-07:00",
            local_timezone="America/Los_Angeles",
            text_format="plain",
            attachments=[],
            entities=[
                Entity.model_validate({
                    "type": "ClientCapabilities",
                    "requiresBotState": True,
                    "supportsListening": True,
                    "supportsTts": True,
                })
            ],
            channel_data={"clientActivityID": "client-activity-001"},
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        # Find the welcome message
        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Hello and Welcome!" in (r.text or "") for r in message_responses
        ), "Welcome message not found in responses"

    @pytest.mark.asyncio
    async def test__send_activity__sends_hello_world__returns_hello_world(
        self, agent_client, response_client
    ):
        """Test that sending 'hello world' returns echo response."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activityA37",
            timestamp="2025-07-30T22:59:55.000Z",
            text="hello world",
            text_format="plain",
            attachments=[],
            entities=[
                Entity.model_validate({
                    "type": "ClientCapabilities",
                    "requiresBotState": True,
                    "supportsListening": True,
                    "supportsTts": True,
                })
            ],
            channel_data={"clientActivityID": "client-act-id"},
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "You said: hello world" in (r.text or "") for r in message_responses
        ), "Echo response not found"

    @pytest.mark.asyncio
    async def test__send_activity__sends_poem__returns_apollo_poem(
        self, agent_client, response_client
    ):
        """Test that sending 'poem' returns poem about Apollo."""
        activity = self.populate(
            type=ActivityTypes.message,
            delivery_mode=DeliveryModes.expect_replies,
            text="poem",
            text_format="plain",
            attachments=[],
        )

        # assert activity == Activity(type="message")
        responses = await agent_client.send_expect_replies(activity)
        popped_responses = await response_client.pop()
        assert len(popped_responses) == 0, "No responses should be in response client for expect_replies"

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"

        # Check for typing indicator and poem content
        has_typing = any(r.type == ActivityTypes.typing for r in responses)
        has_apollo = any(
            "Apollo" in (r.text or "") for r in message_responses
        )
        has_poem_intro = any(
            "Hold on for an awesome poem" in (r.text or "") for r in message_responses
        )

        assert has_poem_intro or has_apollo, "Poem response not found"

    @pytest.mark.asyncio
    async def test__send_activity__sends_seattle_weather__returns_weather(
        self, agent_client, response_client
    ):
        """Test that sending 'w: Seattle for today' returns weather data."""
        activity = self.populate(
            type=ActivityTypes.message,
            text="w: Seattle for today",
            mode=DeliveryModes.expect_replies,
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"

    @pytest.mark.asyncio
    async def test__send_activity__sends_message_with_ac_submit__returns_response(
        self, agent_client, response_client
    ):
        """Test Action.Submit button on Adaptive Card."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activityY1F",
            timestamp="2025-07-30T23:06:37.000Z",
            attachments=[],
            channel_data={
                "postBack": True,
                "clientActivityID": "client-act-id",
            },
            value={
                "verb": "doStuff",
                "id": "doStuff",
                "type": "Action.Submit",
                "test": "test",
                "data": {"name": "test"},
                "usertext": "hello",
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"

        combined_text = " ".join(r.text or "" for r in message_responses)
        assert "doStuff" in combined_text, "Action verb not found in response"
        assert "Action.Submit" in combined_text, "Action.Submit not found in response"
        assert "hello" in combined_text, "User text not found in response"

    @pytest.mark.asyncio
    async def test__send_activity__ends_conversation(
        self, agent_client, response_client
    ):
        """Test that sending 'end' ends the conversation."""
        activity = self.populate(
            type=ActivityTypes.message,
            text="end",
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        # Should have both message and endOfConversation
        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        end_responses = [r for r in responses if r.type == ActivityTypes.end_of_conversation]

        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Ending conversation" in (r.text or "") for r in message_responses
        ), "Ending message not found"
        assert len(end_responses) > 0, "endOfConversation not received"

    @pytest.mark.asyncio
    async def test__send_activity__message_reaction_heart_added(
        self, agent_client, response_client
    ):
        """Test that adding heart reaction returns reaction acknowledgement."""
        activity = self.populate(
            type=ActivityTypes.message_reaction,
            timestamp="2025-07-10T02:25:04.000Z",
            id="1752114287789",
            from_property=ChannelAccount(id="from29ed", aad_object_id="aad-user1"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant6d4",
                id="cpersonal-chat-id",
            ),
            recipient=ChannelAccount(id="basic-agent", name="basic-agent"),
            channel_data={
                "tenant": {"id": "tenant6d4"},
                "legacy": {"replyToId": "legacy_id"},
            },
            reactions_added=[{"type": "heart"}],
            reply_to_id="1752114287789",
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Message Reaction Added: heart" in (r.text or "") 
            for r in message_responses
        ), "Reaction acknowledgement not found"

    @pytest.mark.asyncio
    async def test__send_activity__message_reaction_heart_removed(
        self, agent_client, response_client
    ):
        """Test that removing heart reaction returns reaction acknowledgement."""
        activity = self.populate(
            type=ActivityTypes.message_reaction,
            timestamp="2025-07-10T02:25:04.000Z",
            id="1752114287789",
            from_property=ChannelAccount(id="from29ed", aad_object_id="aad-user1"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant6d4",
                id="cpersonal-chat-id",
            ),
            recipient=ChannelAccount(id="basic-agent", name="basic-agent"),
            channel_data={
                "tenant": {"id": "tenant6d4"},
                "legacy": {"replyToId": "legacy_id"},
            },
            reactions_removed=[{"type": "heart"}],
            reply_to_id="1752114287789",
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Message Reaction Removed: heart" in (r.text or "") 
            for r in message_responses
        ), "Reaction removal acknowledgement not found"

    @pytest.mark.asyncio
    async def test__send_expected_replies__sends_poem__returns_poem(
        self, agent_client, response_client
    ):
        """Test send_expected_replies with poem request."""
        activity = self.populate(
            type=ActivityTypes.message,
            text="poem",
            delivery_mode=DeliveryModes.expect_replies
        )

        responses = await agent_client.send_expect_replies(activity)

        assert len(responses) > 0, "No responses received for expectedReplies"
        combined_text = " ".join(r.text or "" for r in responses)
        assert "Apollo" in combined_text, "Apollo poem not found in responses"

    @pytest.mark.asyncio
    async def test__send_expected_replies__sends_weather__returns_weather(
        self, agent_client, response_client
    ):
        """Test send_expected_replies with weather request."""
        activity = self.populate(
            type=ActivityTypes.message,
            text="w: Seattle for today",
            delivery_mode=DeliveryModes.expect_replies
        )

        responses = await agent_client.send_expect_replies(activity)

        assert len(responses) > 0, "No responses received for expectedReplies"

    @pytest.mark.asyncio
    async def test__send_invoke__basic_invoke__returns_response(
        self, agent_client
    ):
        """Test basic invoke activity."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="invoke456",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            timestamp="2025-07-22T19:21:03.000Z",
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            value={
                "parameters": [{"value": "hi"}],
            },
            service_url="http://localhost:63676/_connector",
        )
        assert activity.type == "invoke"
        response = await agent_client.send_invoke_activity(activity)

        assert response is not None, "No invoke response received"
        assert response.status == 200, f"Unexpected status: {response.status}"

    @pytest.mark.asyncio
    async def test__send_invoke__query_link(
        self, agent_client, response_client
    ):
        """Test invoke for query link."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="invoke_query_link",
            from_property=ChannelAccount(id="user-id-0"),
            name="composeExtension/queryLink",
            value={},
        )

        response = await agent_client.send_invoke_activity(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_invoke__query_package(
        self, agent_client, response_client
    ):
        """Test invoke for query package."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="invoke_query_package",
            from_property=ChannelAccount(id="user-id-0"),
            name="composeExtension/queryPackage",
            value={},
        )

        response = await agent_client.send_invoke_activity(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_invoke__select_item__returns_attachment(
        self, agent_client, response_client
    ):
        """Test invoke for selectItem to return package details."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="invoke123",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            name="composeExtension/selectItem",
            value={
                "@id": "https://www.nuget.org/packages/Newtonsoft.Json/13.0.1",
                "id": "Newtonsoft.Json",
                "version": "13.0.1",
                "description": "Json.NET is a popular high-performance JSON framework for .NET",
                "projectUrl": "https://www.newtonsoft.com/json",
                "iconUrl": "https://www.newtonsoft.com/favicon.ico",
            },
        )

        response = await agent_client.send_invoke_activity(activity)

        assert response is not None, "No invoke response received"
        assert response.status == 200, f"Unexpected status: {response.status}"
        if response.value:
            assert "Newtonsoft.Json" in str(response.value), "Package name not in response"

    @pytest.mark.asyncio
    async def test__send_invoke__adaptive_card_submit__returns_response(
        self, agent_client, response_client
    ):
        """Test invoke for Adaptive Card Action.Submit."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="ac_invoke_001",
            from_property=ChannelAccount(id="user-id-0"),
            name="adaptiveCard/action",
            value={
                "action": {
                    "type": "Action.Submit",
                    "id": "submit-action",
                    "data": {"test": "data"},
                }
            },
        )

        response = await agent_client.send_invoke_activity(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_activity__sends_hi_5__returns_5_responses(
        self, agent_client, response_client
    ):
        """Test that sending 'hi 5' returns 5 message responses."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activity989",
            timestamp="2025-07-22T19:21:03.000Z",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id-hi5",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            text="hi 5",
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) >= 5, f"Expected at least 5 messages, got {len(message_responses)}"

        # Verify each message contains the expected pattern
        for i in range(5):
            combined_text = " ".join(r.text or "" for r in message_responses)
            assert f"[{i}] You said: hi" in combined_text, f"Expected message [{i}] not found"

    @pytest.mark.asyncio
    async def test__send_stream__stream_message__returns_stream_responses(
        self, agent_client, response_client
    ):
        """Test streaming message responses."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activity-stream-001",
            timestamp="2025-06-18T18:47:46.000Z",
            from_property=ChannelAccount(id="user1"),
            conversation=ConversationAccount(id="conversation-stream-001"),
            recipient=ChannelAccount(id="basic-agent", name="basic-agent"),
            text="stream",
            text_format="plain",
            attachments=[],
            entities=[
                Entity.model_validate({
                    "type": "ClientCapabilities",
                    "requiresBotState": True,
                    "supportsListening": True,
                    "supportsTts": True,
                })
            ],
            channel_data={"clientActivityID": "client-activity-stream-001"},
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        # Stream tests just verify responses are received
        assert len(responses) > 0, "No stream responses received"

    @pytest.mark.asyncio
    async def test__send_activity__simulate_message_loop__weather_query(
        self, agent_client, response_client
    ):
        """Test multiple message exchanges simulating message loop."""
        # First message: weather question
        activity1 = self.populate(
            type=ActivityTypes.message,
            text="w: what's the weather?",
            conversation=ConversationAccount(id="conversation-simulate-002"),
        )

        await agent_client.send_activity(activity1)
        responses1 = await response_client.pop()
        assert len(responses1) > 0, "No response to weather question"

        # Second message: location
        activity2 = self.populate(
            type=ActivityTypes.message,
            text="w: Seattle for today",
            conversation=ConversationAccount(id="conversation-simulate-002"),
        )

        await agent_client.send_activity(activity2)
        responses2 = await response_client.pop()
        assert len(responses2) > 0, "No response to location message"