# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the AgentClient class."""

import pytest
from datetime import datetime

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)

from microsoft_agents.testing.core.agent_client import AgentClient, activities_from_ex
from microsoft_agents.testing.core.fluent import ActivityTemplate
from microsoft_agents.testing.core.transport import Transcript, Exchange, Sender


# ============================================================================
# Stub Sender for testing without mocks
# ============================================================================

class StubSender(Sender):
    """A stub sender that records sent activities and returns configurable responses.
    
    This is a real implementation of the Sender protocol for testing purposes,
    not a mock. It captures all sent activities and allows configuring responses.
    """
    
    def __init__(self):
        self.sent_activities: list[Activity] = []
        self.configured_responses: list[Activity] = []
        self.configured_invoke_response: InvokeResponse | None = None
        self.configured_status_code: int = 200
        self.configured_error: str | None = None
    
    def with_responses(self, *responses: Activity) -> "StubSender":
        """Configure responses to return for the next send."""
        self.configured_responses = list(responses)
        return self
    
    def with_invoke_response(self, response: InvokeResponse) -> "StubSender":
        """Configure an invoke response to return."""
        self.configured_invoke_response = response
        return self
    
    def with_error(self, error: str) -> "StubSender":
        """Configure an error to return."""
        self.configured_error = error
        return self
    
    def with_status_code(self, code: int) -> "StubSender":
        """Configure the status code to return."""
        self.configured_status_code = code
        return self
    
    async def send(self, activity: Activity, transcript: Transcript | None = None, **kwargs) -> Exchange:
        """Send an activity and return a configured exchange."""
        self.sent_activities.append(activity)
        
        exchange = Exchange(
            request=activity,
            request_at=datetime.now(),
            status_code=self.configured_status_code,
            responses=list(self.configured_responses),
            invoke_response=self.configured_invoke_response,
            error=self.configured_error,
            response_at=datetime.now(),
        )
        
        if transcript is not None:
            transcript.record(exchange)
        
        return exchange


# ============================================================================
# Test Helper Functions
# ============================================================================

class TestActivitiesFromEx:
    """Tests for the activities_from_ex helper function."""

    def test_empty_exchanges_returns_empty_list(self):
        """activities_from_ex returns empty list for empty exchanges."""
        result = activities_from_ex([])
        assert result == []

    def test_extracts_responses_from_single_exchange(self):
        """activities_from_ex extracts responses from a single exchange."""
        activity1 = Activity(type=ActivityTypes.message, text="Hello")
        activity2 = Activity(type=ActivityTypes.message, text="World")
        exchange = Exchange(responses=[activity1, activity2])
        
        result = activities_from_ex([exchange])
        
        assert len(result) == 2
        assert result[0] == activity1
        assert result[1] == activity2

    def test_extracts_responses_from_multiple_exchanges(self):
        """activities_from_ex extracts responses from multiple exchanges."""
        activity1 = Activity(type=ActivityTypes.message, text="First")
        activity2 = Activity(type=ActivityTypes.message, text="Second")
        activity3 = Activity(type=ActivityTypes.message, text="Third")
        
        exchange1 = Exchange(responses=[activity1])
        exchange2 = Exchange(responses=[activity2, activity3])
        
        result = activities_from_ex([exchange1, exchange2])
        
        assert len(result) == 3
        assert result[0].text == "First"
        assert result[1].text == "Second"
        assert result[2].text == "Third"

    def test_handles_exchanges_with_no_responses(self):
        """activities_from_ex handles exchanges with no responses."""
        exchange1 = Exchange(responses=[])
        exchange2 = Exchange(responses=[Activity(type=ActivityTypes.message, text="Only")])
        
        result = activities_from_ex([exchange1, exchange2])
        
        assert len(result) == 1
        assert result[0].text == "Only"


# ============================================================================
# AgentClient Initialization Tests
# ============================================================================

class TestAgentClientInitialization:
    """Tests for AgentClient initialization."""

    def test_initialization_with_sender_only(self):
        """AgentClient initializes with just a sender."""
        sender = StubSender()
        client = AgentClient(sender=sender)
        
        assert client._sender is sender
        assert isinstance(client._transcript, Transcript)
        assert isinstance(client._template, ActivityTemplate)

    def test_initialization_with_custom_transcript(self):
        """AgentClient uses provided transcript."""
        sender = StubSender()
        transcript = Transcript()
        client = AgentClient(sender=sender, transcript=transcript)
        
        assert client._transcript is transcript

    def test_initialization_with_custom_template(self):
        """AgentClient uses provided template."""
        sender = StubSender()
        template = ActivityTemplate(type=ActivityTypes.message, text="Default")
        client = AgentClient(sender=sender, template=template)

# ============================================================================
# AgentClient Template Tests
# ============================================================================

class TestAgentClientTemplate:
    """Tests for AgentClient template property."""

    def test_get_template(self):
        """template property returns the current template."""
        sender = StubSender()
        template = ActivityTemplate(type=ActivityTypes.message)
        client = AgentClient(sender=sender, template=template)
        
    def test_set_template(self):
        """template property can be set to a new template."""
        sender = StubSender()
        client = AgentClient(sender=sender)
        new_template = ActivityTemplate(type=ActivityTypes.event)
        
        client.template = new_template
        
        assert client.template is new_template


# ============================================================================
# AgentClient Build Activity Tests
# ============================================================================

class TestAgentClientBuildActivity:
    """Tests for the _build_activity method."""

    def test_build_from_string_creates_message_activity(self):
        """_build_activity creates a message activity from string."""
        sender = StubSender()
        client = AgentClient(sender=sender)
        
        activity = client._build_activity("Hello World")
        
        assert activity.type == ActivityTypes.message
        assert activity.text == "Hello World"

    def test_build_from_activity_preserves_activity(self):
        """_build_activity preserves an Activity object."""
        sender = StubSender()
        client = AgentClient(sender=sender)
        original = Activity(type=ActivityTypes.event, name="test-event", value={"key": "value"})
        
        activity = client._build_activity(original)
        
        assert activity.type == ActivityTypes.event
        assert activity.name == "test-event"
        assert activity.value == {"key": "value"}

    def test_build_applies_template_defaults(self):
        """_build_activity applies template defaults."""
        sender = StubSender()
        template = ActivityTemplate(
            channel_id="test-channel",
            locale="en-US",
            **{"from.id": "user-123"}
        )
        client = AgentClient(sender=sender, template=template)
        
        activity = client._build_activity("Hello")
        
        assert activity.channel_id == "test-channel"
        assert activity.locale == "en-US"
        assert activity.from_property.id == "user-123"

    def test_build_activity_overrides_template_defaults(self):
        """Activity values override template defaults."""
        sender = StubSender()
        template = ActivityTemplate(channel_id="default-channel", text="default text")
        client = AgentClient(sender=sender, template=template)
        
        original = Activity(type=ActivityTypes.message, channel_id="custom-channel")
        activity = client._build_activity(original)
        
        assert activity.channel_id == "custom-channel"
        # text should still come from template since original didn't specify it
        assert activity.text == "default text"


# ============================================================================
# AgentClient Send Tests
# ============================================================================

class TestAgentClientSend:
    """Tests for AgentClient.send method."""

    @pytest.mark.asyncio
    async def test_send_with_string(self):
        """send() accepts a string and sends a message activity."""
        sender = StubSender()
        response_activity = Activity(type=ActivityTypes.message, text="Response")
        sender.with_responses(response_activity)
        
        client = AgentClient(sender=sender)
        result = await client.send("Hello")
        
        assert len(sender.sent_activities) == 1
        assert sender.sent_activities[0].type == ActivityTypes.message
        assert sender.sent_activities[0].text == "Hello"
        assert len(result) == 1
        assert result[0].text == "Response"

    @pytest.mark.asyncio
    async def test_send_with_activity(self):
        """send() accepts an Activity object."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="OK"))
        
        client = AgentClient(sender=sender)
        activity = Activity(type=ActivityTypes.event, name="custom-event")
        result = await client.send(activity)
        
        assert len(sender.sent_activities) == 1
        assert sender.sent_activities[0].type == ActivityTypes.event
        assert sender.sent_activities[0].name == "custom-event"

    @pytest.mark.asyncio
    async def test_send_records_to_transcript(self):
        """send() records the exchange in the transcript."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("Hello")
        
        history = client.transcript.history()
        assert len(history) == 1
        assert history[0].request.text == "Hello"
        assert history[0].responses[0].text == "Reply"

    @pytest.mark.asyncio
    async def test_send_multiple_times(self):
        """Multiple sends accumulate in transcript."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("First")
        await client.send("Second")
        await client.send("Third")
        
        history = client.transcript.history()
        assert len(history) == 3
        assert history[0].request.text == "First"
        assert history[1].request.text == "Second"
        assert history[2].request.text == "Third"


# ============================================================================
# AgentClient Ex Send Tests
# ============================================================================

class TestAgentClientExSend:
    """Tests for AgentClient.ex_send method."""

    @pytest.mark.asyncio
    async def test_ex_send_returns_exchanges(self):
        """ex_send() returns Exchange objects."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        result = await client.ex_send("Hello")
        
        assert len(result) == 1
        assert isinstance(result[0], Exchange)
        assert result[0].request.text == "Hello"

    @pytest.mark.asyncio
    async def test_ex_send_with_zero_wait(self):
        """ex_send() with wait=0 returns immediately."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        result = await client.ex_send("Hello", wait=0.0)
        
        assert len(result) == 1


# ============================================================================
# AgentClient Send Expect Replies Tests
# ============================================================================

class TestAgentClientSendExpectReplies:
    """Tests for AgentClient.send_expect_replies method."""

    @pytest.mark.asyncio
    async def test_send_expect_replies_sets_delivery_mode(self):
        """send_expect_replies() sets the delivery_mode to expect_replies."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send_expect_replies("Hello")
        
        assert sender.sent_activities[0].delivery_mode == DeliveryModes.expect_replies

    @pytest.mark.asyncio
    async def test_send_expect_replies_returns_activities(self):
        """send_expect_replies() returns response activities."""
        response1 = Activity(type=ActivityTypes.message, text="Reply 1")
        response2 = Activity(type=ActivityTypes.message, text="Reply 2")
        sender = StubSender().with_responses(response1, response2)
        
        client = AgentClient(sender=sender)
        result = await client.send_expect_replies("Hello")
        
        assert len(result) == 2
        assert result[0].text == "Reply 1"
        assert result[1].text == "Reply 2"

    @pytest.mark.asyncio
    async def test_ex_send_expect_replies_returns_exchanges(self):
        """ex_send_expect_replies() returns Exchange objects."""
        response = Activity(type=ActivityTypes.message, text="Reply")
        sender = StubSender().with_responses(response)
        
        client = AgentClient(sender=sender)
        result = await client.ex_send_expect_replies("Hello")
        
        assert len(result) == 1
        assert isinstance(result[0], Exchange)


# ============================================================================
# AgentClient Send Stream Tests
# ============================================================================

class TestAgentClientSendStream:
    """Tests for AgentClient.send_stream method."""

    @pytest.mark.asyncio
    async def test_send_stream_sets_delivery_mode(self):
        """send_stream() sets the delivery_mode to stream."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))

        client = AgentClient(sender=sender)
        await client.send_stream("Hello")

        assert sender.sent_activities[0].delivery_mode == DeliveryModes.stream

    @pytest.mark.asyncio
    async def test_send_stream_returns_activities(self):
        """send_stream() returns response activities."""
        response1 = Activity(type=ActivityTypes.message, text="Stream reply 1")
        response2 = Activity(type=ActivityTypes.message, text="Stream reply 2")
        sender = StubSender().with_responses(response1, response2)

        client = AgentClient(sender=sender)
        result = await client.send_stream("Hello")

        assert [a.text for a in result] == ["Stream reply 1", "Stream reply 2"]

    @pytest.mark.asyncio
    async def test_ex_send_stream_returns_exchanges(self):
        """ex_send_stream() returns Exchange objects."""
        response = Activity(type=ActivityTypes.message, text="Reply")
        sender = StubSender().with_responses(response)

        client = AgentClient(sender=sender)
        result = await client.ex_send_stream("Hello")

        assert len(result) == 1
        assert isinstance(result[0], Exchange)
        assert result[0].request is not None
        assert result[0].request.delivery_mode == DeliveryModes.stream


# ============================================================================
# AgentClient Invoke Tests
# ============================================================================

class TestAgentClientInvoke:
    """Tests for AgentClient.invoke method."""

    @pytest.mark.asyncio
    async def test_invoke_returns_invoke_response(self):
        """invoke() returns the InvokeResponse."""
        sender = StubSender()
        invoke_response = InvokeResponse(status=200, body={"result": "success"})
        sender.with_invoke_response(invoke_response)
        
        client = AgentClient(sender=sender)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")
        result = await client.invoke(activity)
        
        assert result.status == 200
        assert result.body == {"result": "success"}

    @pytest.mark.asyncio
    async def test_invoke_raises_for_non_invoke_activity(self):
        """invoke() raises ValueError for non-invoke activity type."""
        sender = StubSender()
        client = AgentClient(sender=sender)
        activity = Activity(type=ActivityTypes.message, text="Hello")
        
        with pytest.raises(ValueError, match="Activity type must be 'invoke'"):
            await client.invoke(activity)

    @pytest.mark.asyncio
    async def test_invoke_raises_when_no_response(self):
        """invoke() raises RuntimeError when no InvokeResponse received."""
        sender = StubSender()
        # No invoke response configured
        
        client = AgentClient(sender=sender)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")
        
        with pytest.raises(RuntimeError, match="No InvokeResponse received"):
            await client.invoke(activity)

    @pytest.mark.asyncio
    async def test_invoke_raises_when_error_present(self):
        """invoke() raises Exception when error is present in exchange."""
        sender = StubSender().with_error("Connection failed")
        
        client = AgentClient(sender=sender)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")
        
        with pytest.raises(Exception, match="Connection failed"):
            await client.invoke(activity)

    @pytest.mark.asyncio
    async def test_ex_invoke_returns_exchange(self):
        """ex_invoke() returns the Exchange object."""
        sender = StubSender()
        invoke_response = InvokeResponse(status=200, body={"result": "ok"})
        sender.with_invoke_response(invoke_response)
        
        client = AgentClient(sender=sender)
        activity = Activity(type=ActivityTypes.invoke, name="test/invoke")
        result = await client.ex_invoke(activity)
        
        assert isinstance(result, Exchange)
        assert result.invoke_response.status == 200


# ============================================================================
# AgentClient Transcript Access Tests
# ============================================================================

class TestAgentClientTranscriptAccess:
    """Tests for AgentClient transcript access methods."""

    @pytest.mark.asyncio
    async def test_history_returns_all_activities(self):
        """history() returns all activities from transcript."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("First")
        await client.send("Second")
        
        history = client.history()
        
        # 2 responses (one per send)
        assert len(history) == 2
        assert history[0].text == "Reply"
        assert history[1].text == "Reply"

    @pytest.mark.asyncio
    async def test_recent_returns_activities(self):
        """recent() returns recent activities."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("Hello")
        
        recent = client.recent()
        assert len(recent) == 1
        assert recent[0].text == "Reply"

    @pytest.mark.asyncio
    async def test_ex_history_returns_all_exchanges(self):
        """ex_history() returns all exchanges from transcript."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("First")
        await client.send("Second")
        
        history = client.ex_history()
        
        assert len(history) == 2
        assert history[0].request.text == "First"
        assert history[1].request.text == "Second"

    @pytest.mark.asyncio
    async def test_ex_recent_returns_exchanges(self):
        """ex_recent() returns recent exchanges."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("Hello")
        
        recent = client.ex_recent()
        assert len(recent) == 1
        assert recent[0].request.text == "Hello"

    @pytest.mark.asyncio
    async def test_clear_clears_transcript(self):
        """clear() clears the transcript history."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("Hello")
        assert len(client.history()) == 1
        
        client.clear()
        
        assert len(client.history()) == 0


# ============================================================================
# AgentClient Select/Expect Tests
# ============================================================================

class TestAgentClientSelectExpect:
    """Tests for AgentClient select and expect methods."""

    @pytest.mark.asyncio
    async def test_select_returns_select_instance(self):
        """select() returns a Select instance."""
        from microsoft_agents.testing.core.fluent import Select
        
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("Hello")
        
        result = client.select()
        assert isinstance(result, Select)

    @pytest.mark.asyncio
    async def test_ex_select_returns_select_with_exchanges(self):
        """ex_select() returns a Select instance with exchanges."""
        from microsoft_agents.testing.core.fluent import Select
        
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        client = AgentClient(sender=sender)
        await client.send("Hello")
        
        result = client.ex_select()
        assert isinstance(result, Select)


# ============================================================================
# AgentClient Child Tests
# ============================================================================

class TestAgentClientChild:
    """Tests for AgentClient.child method."""

    def test_child_shares_sender(self):
        """child() creates a client that shares the same sender."""
        sender = StubSender()
        parent = AgentClient(sender=sender)
        child = parent.child()
        
        assert child._sender is parent._sender

    def test_child_has_child_transcript(self):
        """child() creates a client with a child transcript."""
        sender = StubSender()
        parent = AgentClient(sender=sender)
        child = parent.child()
        
        # Child transcript should have parent as its parent
        assert child._transcript._parent is parent._transcript

    @pytest.mark.asyncio
    async def test_child_sends_propagate_to_parent(self):
        """Exchanges from child propagate to parent transcript."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        parent = AgentClient(sender=sender)
        child = parent.child()
        
        await child.send("From child")
        
        # Should be in both transcripts
        assert len(child.ex_history()) == 1
        assert len(parent.ex_history()) == 1
        assert parent.ex_history()[0].request.text == "From child"

    @pytest.mark.asyncio
    async def test_parent_and_child_independent_sends(self):
        """Parent and child can send independently."""
        sender = StubSender()
        sender.with_responses(Activity(type=ActivityTypes.message, text="Reply"))
        
        parent = AgentClient(sender=sender)
        child = parent.child()
        
        await parent.send("From parent")
        await child.send("From child")
        
        assert len(parent.ex_history()) == 2
        assert len(child.ex_history()) == 2