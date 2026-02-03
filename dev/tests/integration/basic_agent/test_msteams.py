import pytest
import asyncio

from typing import cast

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    DeliveryModes,
    Entity,
)
from microsoft_agents.testing import AgentClient, Expect

from .test_basic_agent_base import TestBasicAgentBase


class TestBasicAgentMSTeams(TestBasicAgentBase):
    """Test MSTeams channel for basic agent."""

    @pytest.mark.asyncio
    async def test__send_activity__conversation_update__returns_welcome_message(
        self, agent_client: AgentClient
    ):
        """Test that ConversationUpdate activity returns welcome message."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity, wait=1.0)

        agent_client.expect().that_for_one(
            type="message",
            text="~Hello and Welcome!"
        )

    @pytest.mark.asyncio
    async def test__send_activity__sends_hello_world__returns_hello_world(
        self, agent_client: AgentClient
    ):
        """Test that sending 'hello world' returns echo response."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity, wait=1.0)

        agent_client.expect().that_for_one(
            type="message",
            text="~You said: hello world"
        )

    @pytest.mark.asyncio
    async def test__send_activity__sends_poem__returns_apollo_poem(
        self, agent_client: AgentClient
    ):
        """Test that sending 'poem' returns poem about Apollo."""
        activity = agent_client.template.create(dict(
            type=ActivityTypes.message,
            delivery_mode=DeliveryModes.expect_replies,
            text="poem",
            text_format="plain",
            attachments=[],
        ))

        responses = await agent_client.send_expect_replies(activity)

        await asyncio.sleep(1.0)  # Allow time for responses to be processed

        assert len(agent_client.history()) == len(responses), "History length mismatch with expect_replies responses"

        Expect(responses).that_for_one(type=ActivityTypes.typing)
        Expect(responses).that_for_one(text="~Apollo")
        Expect(responses).that_for_one(text="~Hold on for an awesome poem")

    @pytest.mark.asyncio
    async def test__send_activity__sends_seattle_weather__returns_weather(
        self, agent_client: AgentClient
    ):
        """Test that sending weather query returns weather data."""
        activity = agent_client.template.create(dict(
            type=ActivityTypes.message,
            text="w: Seattle for today",
            mode=DeliveryModes.expect_replies,
        ))
        await agent_client.send(activity)
        agent_client.expect().that_for_any(
            type=ActivityTypes.typing
        )

    @pytest.mark.asyncio
    async def test__send_activity__sends_message_with_ac_submit__returns_response(
        self, agent_client: AgentClient
    ):
        """Test Action.Submit button on Adaptive Card."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity)
        # Expect a response that includes the verb, action type, and user text
        agent_client.expect().that_for_any(
            type="message",
            text=lambda x: "doStuff" in x and "Action.Submit" in x and "hello" in x
        )

    @pytest.mark.asyncio
    async def test__send_activity__ends_conversation(
        self, agent_client: AgentClient
    ):
        """Test that sending 'end' ends the conversation."""
        await agent_client.send("end", wait=1.0)
        agent_client.expect()\
            .that_for_any(type=ActivityTypes.message)\
            .that_for_any(type=ActivityTypes.end_of_conversation)\
            .that_for_any(text="~Ending conversation")

    @pytest.mark.asyncio
    async def test__send_activity__message_reaction_heart_added(
        self, agent_client: AgentClient
    ):
        """Test that adding heart reaction returns reaction acknowledgement."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity, wait=1.0)
        agent_client.expect().that_for_one(
            type=ActivityTypes.message,
            text="~Message Reaction Added: heart"
        )

    @pytest.mark.asyncio
    async def test__send_activity__message_reaction_heart_removed(
        self, agent_client: AgentClient,
    ):
        """Test that removing heart reaction returns reaction acknowledgement."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity, wait=1.0)
        agent_client.expect().that_for_any(
            type="message",
            text="~Message Reaction Removed: heart"
        )

    @pytest.mark.asyncio
    async def test__send_expected_replies__sends_poem__returns_poem(
        self, agent_client: AgentClient
    ):
        """Test send_expected_replies with poem request."""
        responses = await agent_client.send_expect_replies("poem")
        assert len(responses) > 0, "No responses received for expectedReplies"
        Expect(responses).that_for_any(text="~Apollo")

    @pytest.mark.asyncio
    async def test__send_expected_replies__sends_weather__returns_weather(
        self, agent_client: AgentClient
    ):
        """Test send_expected_replies with weather request."""
        responses = await agent_client.send_expect_replies("w: Seattle for today")
        assert len(responses) > 0, "No responses received for expectedReplies"

    @pytest.mark.asyncio
    async def test__send_invoke__basic_invoke__returns_response(
        self, agent_client: AgentClient
    ):
        """Test basic invoke activity."""
        activity = agent_client.template.create(dict(
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
        ))
        assert activity.type == "invoke"

        response = await agent_client.invoke(activity)

        assert response is not None, "No invoke response received"
        assert response.status == 200, f"Unexpected status: {response.status}"

    @pytest.mark.asyncio
    async def test__send_invoke__query_link(
        self, agent_client: AgentClient
    ):
        """Test invoke for query link."""
        activity = agent_client.template.create(dict(
            type=ActivityTypes.invoke,
            id="invoke_query_link",
            from_property=ChannelAccount(id="user-id-0"),
            name="composeExtension/queryLink",
            value={
                "url": "https://github.com/microsoft/Agents-for-net/blob/users/tracyboehrer/cards-sample/src/samples/Teams/TeamsAgent/TeamsAgent.cs",
            },
        ))
        response = await agent_client.invoke(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_invoke__query_package(
        self, agent_client: AgentClient
    ):
        """Test invoke for query package."""
        activity = agent_client.template.create(dict(
            type=ActivityTypes.invoke,
            id="invoke_query_package",
            from_property=ChannelAccount(id="user-id-0"),
            name="composeExtension/query",
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
        ))

        response = await agent_client.invoke(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_invoke__select_item__returns_attachment(
        self, agent_client: AgentClient
    ):
        """Test invoke for selectItem to return package details."""
        activity = agent_client.template.create(dict(
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
        ))

        response = await agent_client.invoke(activity)

        assert response is not None, "No invoke response received"
        assert response.status == 200, f"Unexpected status: {response.status}"
        if response.body:
            assert "Newtonsoft.Json" in str(response.body), "Package name not in response"

    @pytest.mark.asyncio
    async def test__send_invoke__adaptive_card_execute__returns_response(
        self, agent_client: AgentClient
    ):
        """Test invoke for Adaptive Card Action.Execute."""
        activity = agent_client.template.create(dict(
            type=ActivityTypes.invoke,
            id="ac_invoke_001",
            from_property=ChannelAccount(id="user-id-0"),
            name="adaptiveCard/action",
            value={
                "action": {
                    "type": "Action.Execute",
                    "title": "Execute doStuff",
                    "verb": "doStuff",
                    "data": {"usertext": "hi"},
                },
                "trigger": "manual",
            },
        ))

        response = await agent_client.invoke(activity)
        assert response is not None, "No invoke response received"

    @pytest.mark.asyncio
    async def test__send_activity__sends_hi_5__returns_5_responses(
        self, agent_client: AgentClient
    ):
        """Test that sending 'hi 5' returns 5 message responses."""
        activity = agent_client.template.create(dict(
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
        ))

        responses = await agent_client.send(activity, wait=3.0)

        assert len(responses) >= 5, f"Expected at least 5 responses, got {len(responses)}"

        message_responses = cast(list[Activity], agent_client.select().where(type=ActivityTypes.message).get())

        # Verify each message contains the expected pattern
        for i in range(5):
            combined_text = " ".join(r.text or "" for r in message_responses)
            assert f"[{i}] You said: hi" in combined_text, f"Expected message [{i}] not found"

    @pytest.mark.asyncio
    async def test__send_stream__stream_message__returns_stream_responses(
        self, agent_client: AgentClient
    ):
        """Test streaming message responses."""
        activity = agent_client.template.create(dict(
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
        ))

        responses = await agent_client.send(activity, wait=1.0)
        # Stream tests just verify responses are received
        assert len(responses) > 0, "No stream responses received"

    @pytest.mark.asyncio
    async def test__send_activity__start_teams_meeting__expect_message(
        self, agent_client: AgentClient
    ):
        """Test Teams meeting start event."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity, wait=1.0)
        agent_client.expect().that_for_one(
            type=ActivityTypes.message,
            text="~Meeting started with ID: meeting-12345"
        )

    @pytest.mark.asyncio
    async def test__send_activity__end_teams_meeting__expect_message(
        self, agent_client: AgentClient
    ):
        """Test Teams meeting end event."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity, wait=1.0)
        agent_client.expect().that_for_one(
            type=ActivityTypes.message,
            text="~Meeting ended with ID: meeting-12345"
        )

    @pytest.mark.asyncio
    async def test__send_activity__participant_joins_teams_meeting__expect_message(
        self, agent_client: AgentClient
    ):
        """Test Teams meeting participant join event."""
        activity = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity, wait=1.0)
        agent_client.expect().that_for_one(
            type=ActivityTypes.message,
            text="~Welcome to the meeting!"
        )

    @pytest.mark.asyncio
    async def test__send_activity__edit_message__receive_update(
        self, agent_client: AgentClient
    ):
        """Test message edit event."""
        # First send an initial message
        activity1 = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity1, wait=1.0)
        agent_client.expect().that_for_one(
            type=ActivityTypes.message,
            text="~Hello"
        )

        # Then send a message update
        activity2 = agent_client.template.create(dict(
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
        ))

        await agent_client.send(activity2, wait=1.0)
        agent_client.expect().that_for_any(
            type=ActivityTypes.message,
            text="~Message Edited: activity989"
        )

    @pytest.mark.asyncio
    async def test__send_activity__simulate_message_loop__weather_query(
        self, agent_client: AgentClient,
    ):
        """Test multiple message exchanges simulating message loop."""
        # First message: weather question
        activity1 = agent_client.template.create(dict(
            type=ActivityTypes.message,
            text="w: what's the weather?",
            conversation=ConversationAccount(id="conversation-simulate-002"),
        ))

        responses1 = await agent_client.send(activity1, wait=1.0)
        assert len(responses1) > 0, "No response to weather question"

        # Second message: location
        activity2 = agent_client.template.create(dict(
            type=ActivityTypes.message,
            text="w: Seattle for today",
            conversation=ConversationAccount(id="conversation-simulate-002"),
        ))

        responses2 = await agent_client.send(activity2, wait=1.0)
        assert len(responses2) > 0, "No response to location message"
