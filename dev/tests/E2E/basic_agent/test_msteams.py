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

class TestBasicAgentMSTeams(TestBasicAgent):
    """Test MSTeams channel for basic agent."""

    OUTGOING_PARENT = {
        "channel_id": "msteams",
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
            id="activity123",
            timestamp="2025-06-23T19:48:15.625+00:00",
            service_url="http://localhost:62491/_connector",
            from_property=ChannelAccount(id="user-id-0", aad_object_id="aad-user-alex", role="user"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            members_added=[
                ChannelAccount(id="user-id-0", aad_object_id="aad-user-alex"),
                ChannelAccount(id="bot-001"),
            ],
            members_removed=[],
            reactions_added=[],
            reactions_removed=[],
            attachments=[],
            entities=[],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
            listen_for=[],
            text_highlights=[],
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
            id="activity-hello-msteams-001",
            timestamp="2025-06-18T18:47:46.000Z",
            local_timestamp="2025-06-18T11:47:46.000-07:00",
            local_timezone="America/Los_Angeles",
            from_property=ChannelAccount(id="user1", name=""),
            conversation=ConversationAccount(id="conversation-hello-msteams-001"),
            recipient=ChannelAccount(id="basic-agent@sometext", name="basic-agent"),
            text_format="plain",
            text="hello world",
            attachments=[],
            entities=[
                Entity.model_validate({
                    "type": "ClientCapabilities",
                    "requiresBotState": True,
                    "supportsListening": True,
                    "supportsTts": True,
                })
            ],
            channel_data={
                "clientActivityID": "client-activity-hello-msteams-001",
            },
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
            text="poem",
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            text_format="plain",
            from_property=ChannelAccount(id="user1", name="User"),
            conversation=ConversationAccount(id="conversation-abc123"),
            recipient=ChannelAccount(id="bot1", name="Bot"),
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        # Check for typing indicator and poem content
        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"

        has_apollo = any(
            "Apollo" in (r.text or "") for r in message_responses
        )
        has_poem_intro = any(
            "Hold on for an awesome poem about Apollo" in (r.text or "") for r in message_responses
        )

        assert has_poem_intro or has_apollo, "Poem response not found"

    @pytest.mark.asyncio
    async def test__send_activity__sends_seattle_weather__returns_weather(
        self, agent_client, response_client
    ):
        """Test that sending weather query returns weather data."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:60209/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            text_format="plain",
            text="w: What's the weather in Seattle today?",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        # Weather tests just verify responses are received
        assert len(responses) > 0, "No responses received"

    @pytest.mark.asyncio
    async def test__send_activity__sends_message_with_ac_submit__returns_response(
        self, agent_client, response_client
    ):
        """Test Action.Submit button on Adaptive Card."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activity123",
            timestamp="2025-06-27T17:24:16.000Z",
            local_timestamp="2025-06-27T17:24:16.000Z",
            local_timezone="America/Los_Angeles",
            service_url="https://smba.trafficmanager.net/amer/",
            from_property=ChannelAccount(id="from29ed", name="Basic User", aad_object_id="aad-user1"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant6d4",
                id="cpersonal-chat-id",
            ),
            recipient=ChannelAccount(id="basic-agent@sometext", name="basic-agent"),
            reply_to_id="activity123",
            value={
                "verb": "doStuff",
                "id": "doStuff",
                "type": "Action.Submit",
                "test": "test",
                "data": {"name": "test"},
                "usertext": "hello",
            },
            channel_data={
                "tenant": {"id": "tenant6d4"},
                "source": {"name": "message"},
                "legacy": {"replyToId": "legacy_id"},
            },
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
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
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            text_format="plain",
            from_property=ChannelAccount(id="user1", name="User"),
            conversation=ConversationAccount(id="conversation-abc123"),
            recipient=ChannelAccount(id="bot1", name="Bot"),
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        # Should have both message and endOfConversation
        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        end_responses = [r for r in responses if r.type == ActivityTypes.end_of_conversation]

        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Ending conversation..." in (r.text or "") for r in message_responses
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
            id="activity175",
            from_property=ChannelAccount(id="from29ed", aad_object_id="aad-user1"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant6d4",
                id="cpersonal-chat-id",
            ),
            recipient=ChannelAccount(id="basic-agent@sometext", name="basic-agent"),
            channel_data={
                "tenant": {"id": "tenant6d4"},
                "legacy": {"replyToId": "legacy_id"},
            },
            reactions_added=[{"type": "heart"}],
            reply_to_id="activity175",
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
            timestamp="2025-07-10T02:30:00.000Z",
            id="activity175",
            from_property=ChannelAccount(id="from29ed", aad_object_id="d6dab"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant6d4",
                id="cpersonal-chat-id",
            ),
            recipient=ChannelAccount(id="basic-agent@sometext", name="basic-agent"),
            channel_data={
                "tenant": {"id": "tenant6d4"},
                "legacy": {"replyToId": "legacy_id"},
            },
            reactions_removed=[{"type": "heart"}],
            reply_to_id="activity175",
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
        self, agent_client
    ):
        """Test send_expected_replies with poem request."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:60209/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            text_format="plain",
            text="poem",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
            delivery_mode=DeliveryModes.expect_replies
        )

        responses = await agent_client.send_expect_replies(activity)

        assert len(responses) > 0, "No responses received for expectedReplies"
        combined_text = " ".join(r.text or "" for r in responses)
        assert "Apollo" in combined_text, "Apollo poem not found in responses"

    @pytest.mark.asyncio
    async def test__send_expected_replies__sends_weather__returns_weather(
        self, agent_client
    ):
        """Test send_expected_replies with weather request."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:60209/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            text_format="plain",
            text="w: What's the weather in Seattle today?",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
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
            timestamp="2025-07-22T19:21:03.000Z",
            local_timestamp="2025-07-22T12:21:03.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:63676/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
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
        )
        assert activity.type == "invoke"
        response = await agent_client.send_invoke_activity(activity)

        assert response is not None, "No invoke response received"
        assert response.status == 200, f"Unexpected status: {response.status}"

    @pytest.mark.asyncio
    async def test__send_invoke__query_link(
        self, agent_client
    ):
        """Test invoke for query link."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="invoke123",
            timestamp="2025-07-08T22:53:24.000Z",
            local_timestamp="2025-07-08T15:53:24.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:52065/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            name="composeExtension/queryLink",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "source": {"name": "compose"},
                "tenant": {"id": "tenant-001"},
            },
            value={
                "url": "https://github.com/microsoft/Agents-for-net/blob/users/tracyboehrer/cards-sample/src/samples/Teams/TeamsAgent/TeamsAgent.cs",
            },
        )

        response = await agent_client.send_invoke_activity(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_invoke__query_package(
        self, agent_client
    ):
        """Test invoke for query package."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="invoke123",
            timestamp="2025-07-08T22:53:24.000Z",
            local_timestamp="2025-07-08T15:53:24.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:52065/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            name="composeExtension/query",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "source": {"name": "compose"},
                "tenant": {"id": "tenant-001"},
            },
            value={
                "commandId": "findNuGetPackage",
                "parameters": [
                    {"name": "NuGetPackageName", "value": "Newtonsoft.Json"}
                ],
                "queryOptions": {
                    "skip": 0,
                    "count": 10
                },
            },
        )

        response = await agent_client.send_invoke_activity(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_invoke__select_item__returns_attachment(
        self, agent_client
    ):
        """Test invoke for selectItem to return package details."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            id="invoke123",
            timestamp="2025-07-08T22:53:24.000Z",
            local_timestamp="2025-07-08T15:53:24.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:52065/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            name="composeExtension/selectItem",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "source": {"name": "compose"},
                "tenant": {"id": "tenant-001"},
            },
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

    @pytest.mark.asyncio
    async def test__send_invoke__adaptive_card_execute__returns_response(
        self, agent_client
    ):
        """Test invoke for Adaptive Card Action.Execute."""
        activity = self.populate(
            type=ActivityTypes.invoke,
            name="adaptiveCard/action",
            from_property=ChannelAccount(id="user1"),
            conversation=ConversationAccount(id="conversation-abc123"),
            recipient=ChannelAccount(id="bot1", name="Bot"),
            value={
                "action": {
                    "type": "Action.Execute",
                    "title": "Execute doStuff",
                    "verb": "doStuff",
                    "data": {"usertext": "hi"},
                },
                "trigger": "manual",
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
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:60209/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            text_format="plain",
            text="hi 5",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) >= 5, f"Expected at least 5 messages, got {len(message_responses)}"

        # Verify each message contains the expected pattern
        combined_text = " ".join(r.text or "" for r in message_responses)
        for i in range(5):
            assert f"[{i}] You said: hi" in combined_text, f"Expected message [{i}] not found"

    @pytest.mark.asyncio
    async def test__send_stream__stream_message__returns_stream_responses(
        self, agent_client, response_client
    ):
        """Test streaming message responses."""
        activity = self.populate(
            type=ActivityTypes.message,
            id="activityEvS8",
            timestamp="2025-06-18T18:47:46.000Z",
            local_timestamp="2025-06-18T11:47:46.000-07:00",
            local_timezone="America/Los_Angeles",
            from_property=ChannelAccount(id="user1", name=""),
            conversation=ConversationAccount(id="conv1"),
            recipient=ChannelAccount(id="basic-agent@sometext", name="basic-agent"),
            text_format="plain",
            text="stream",
            attachments=[],
            entities=[
                Entity.model_validate({
                    "type": "ClientCapabilities",
                    "requiresBotState": True,
                    "supportsListening": True,
                    "supportsTts": True,
                })
            ],
            channel_data={"clientActivityID": "activityAZ8"},
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        # Stream tests just verify responses are received
        assert len(responses) > 0, "No stream responses received"

    @pytest.mark.asyncio
    async def test__send_activity__start_teams_meeting__expect_message(
        self, agent_client, response_client
    ):
        """Test Teams meeting start event."""
        activity = self.populate(
            type=ActivityTypes.event,
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            text_format="plain",
            name="application/vnd.microsoft.meetingStart",
            from_property=ChannelAccount(id="user-001", name="Jordan Lee"),
            conversation=ConversationAccount(id="conversation-abc123"),
            recipient=ChannelAccount(id="bot-001", name="TeamHelperBot"),
            service_url="https://smba.trafficmanager.net/amer/",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
            value={
                "trigger": "onMeetingStart",
                "id": "meeting-12345",
                "title": "Quarterly Planning Meeting",
                "startTime": "2025-07-28T21:00:00Z",
                "joinUrl": "https://teams.microsoft.com/l/meetup-join/...",
                "meetingType": "scheduled",
                "meeting": {
                    "organizer": {
                        "id": "user-002",
                        "name": "Morgan Rivera",
                    },
                    "participants": [
                        {"id": "user-001", "name": "Jordan Lee"},
                        {"id": "user-003", "name": "Taylor Kim"},
                        {"id": "user-004", "name": "Riley Chen"},
                    ],
                    "location": "Microsoft Teams Meeting",
                },
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Meeting started with ID: meeting-12345" in (r.text or "") 
            for r in message_responses
        ), "Meeting start message not found"

    @pytest.mark.asyncio
    async def test__send_activity__end_teams_meeting__expect_message(
        self, agent_client, response_client
    ):
        """Test Teams meeting end event."""
        activity = self.populate(
            type=ActivityTypes.event,
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            text_format="plain",
            name="application/vnd.microsoft.meetingEnd",
            from_property=ChannelAccount(id="user-001", name="Jordan Lee"),
            conversation=ConversationAccount(id="conversation-abc123"),
            recipient=ChannelAccount(id="bot-001", name="TeamHelperBot"),
            service_url="https://smba.trafficmanager.net/amer/",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
            value={
                "trigger": "onMeetingStart",
                "id": "meeting-12345",
                "title": "Quarterly Planning Meeting",
                "endTime": "2025-07-28T21:00:00Z",
                "joinUrl": "https://teams.microsoft.com/l/meetup-join/...",
                "meetingType": "scheduled",
                "meeting": {
                    "organizer": {
                        "id": "user-002",
                        "name": "Morgan Rivera",
                    },
                    "participants": [
                        {"id": "user-001", "name": "Jordan Lee"},
                        {"id": "user-003", "name": "Taylor Kim"},
                        {"id": "user-004", "name": "Riley Chen"},
                    ],
                    "location": "Microsoft Teams Meeting",
                },
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Meeting ended with ID: meeting-12345" in (r.text or "") 
            for r in message_responses
        ), "Meeting end message not found"

    @pytest.mark.asyncio
    async def test__send_activity__participant_joins_teams_meeting__expect_message(
        self, agent_client, response_client
    ):
        """Test Teams meeting participant join event."""
        activity = self.populate(
            type=ActivityTypes.event,
            id="activity989",
            timestamp="2025-07-07T21:24:15.000Z",
            local_timestamp="2025-07-07T14:24:15.000-07:00",
            local_timezone="America/Los_Angeles",
            text_format="plain",
            name="application/vnd.microsoft.meetingParticipantJoin",
            from_property=ChannelAccount(id="user-001", name="Jordan Lee"),
            conversation=ConversationAccount(id="conversation-abc123"),
            recipient=ChannelAccount(id="bot-001", name="TeamHelperBot"),
            service_url="https://smba.trafficmanager.net/amer/",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
            value={
                "trigger": "onMeetingStart",
                "id": "meeting-12345",
                "title": "Quarterly Planning Meeting",
                "endTime": "2025-07-28T21:00:00Z",
                "joinUrl": "https://teams.microsoft.com/l/meetup-join/...",
                "meetingType": "scheduled",
                "meeting": {
                    "organizer": {
                        "id": "user-002",
                        "name": "Morgan Rivera",
                    },
                    "participants": [
                        {"id": "user-001", "name": "Jordan Lee"},
                        {"id": "user-003", "name": "Taylor Kim"},
                        {"id": "user-004", "name": "Riley Chen"},
                    ],
                    "location": "Microsoft Teams Meeting",
                },
            },
        )

        await agent_client.send_activity(activity)
        responses = await response_client.pop()

        message_responses = [r for r in responses if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Welcome to the meeting!" in (r.text or "") 
            for r in message_responses
        ), "Meeting welcome message not found"

    @pytest.mark.asyncio
    async def test__send_activity__edit_message__receive_update(
        self, agent_client, response_client
    ):
        """Test message edit event."""
        # First send an initial message
        activity1 = self.populate(
            type=ActivityTypes.message,
            id="activity989",
            timestamp="2025-07-07T21:24:15.930Z",
            local_timestamp="2025-07-07T14:24:15.930-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:60209/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            text_format="plain",
            text="Hello",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "tenant": {"id": "tenant-001"},
            },
        )

        await agent_client.send_activity(activity1)
        responses1 = await response_client.pop()

        message_responses = [r for r in responses1 if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Hello" in (r.text or "") for r in message_responses
        ), "Initial message not found"

        # Then send a message update
        activity2 = self.populate(
            type=ActivityTypes.message_update,
            id="activity989",
            timestamp="2025-07-07T21:24:15.930Z",
            local_timestamp="2025-07-07T14:24:15.930-07:00",
            local_timezone="America/Los_Angeles",
            service_url="http://localhost:60209/_connector",
            from_property=ChannelAccount(id="user-id-0", name="Alex Wilber", aad_object_id="aad-user-alex"),
            conversation=ConversationAccount(
                conversation_type="personal",
                tenant_id="tenant-001",
                id="personal-chat-id",
            ),
            recipient=ChannelAccount(id="bot-001", name="Test Bot"),
            text_format="plain",
            text="This is the updated message content.",
            entities=[
                Entity.model_validate({
                    "type": "clientInfo",
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "America/Los_Angeles",
                })
            ],
            channel_data={
                "eventType": "editMessage",
                "tenant": {"id": "tenant-001"},
            },
        )

        await agent_client.send_activity(activity2)
        responses2 = await response_client.pop()

        message_responses = [r for r in responses2 if r.type == ActivityTypes.message]
        assert len(message_responses) > 0, "No message response received"
        assert any(
            "Message Edited: activity989" in (r.text or "") 
            for r in message_responses
        ), "Message edited acknowledgement not found"
