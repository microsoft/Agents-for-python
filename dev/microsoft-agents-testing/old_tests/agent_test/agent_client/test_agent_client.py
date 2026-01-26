# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.activity import Activity, ActivityTypes, DeliveryModes, InvokeResponse

from microsoft_agents.testing.agent_test.agent_client.agent_client import AgentClient
from microsoft_agents.testing.agent_test.agent_client.response_collector import ResponseCollector
from microsoft_agents.testing.agent_test.agent_client.sender_client import SenderClient
from microsoft_agents.testing.utils import ActivityTemplate


class TestAgentClientInit:
    """Test AgentClient initialization."""

    def test_init_sets_sender(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        client = AgentClient(sender, collector)
        assert client._sender is sender

    def test_init_sets_collector(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        client = AgentClient(sender, collector)
        assert client._collector is collector

    def test_init_creates_default_activity_template_when_none_provided(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        client = AgentClient(sender, collector)
        assert client._activity_template == ActivityTemplate()

    def test_init_uses_provided_activity_template(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        template = ActivityTemplate({"channel_id": "test-channel"})
        client = AgentClient(sender, collector, activity_template=template)
        assert client._activity_template is template

    def test_init_raises_value_error_when_sender_is_none(self):
        collector = MagicMock(spec=ResponseCollector)
        with pytest.raises(ValueError, match="Sender and collector must be provided"):
            AgentClient(None, collector)

    def test_init_raises_value_error_when_collector_is_none(self):
        sender = MagicMock(spec=SenderClient)
        with pytest.raises(ValueError, match="Sender and collector must be provided"):
            AgentClient(sender, None)

    def test_init_raises_value_error_when_both_are_none(self):
        with pytest.raises(ValueError, match="Sender and collector must be provided"):
            AgentClient(None, None)


class TestAgentClientActivityTemplateProperty:
    """Test AgentClient.activity_template property."""

    def test_activity_template_getter_returns_template(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        template = ActivityTemplate({"channel_id": "test-channel"})
        client = AgentClient(sender, collector, activity_template=template)
        assert client.activity_template is template

    def test_activity_template_setter_updates_template(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        client = AgentClient(sender, collector)
        
        new_template = ActivityTemplate({"channel_id": "new-channel"})
        client.activity_template = new_template
        
        assert client.activity_template is new_template


class TestAgentClientActivity:
    """Test AgentClient.activity method."""

    def test_activity_creates_activity_from_string(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        client = AgentClient(sender, collector)
        
        result = client.activity("hello world")
        
        assert isinstance(result, Activity)
        assert result.text == "hello world"
        assert result.type == ActivityTypes.message

    def test_activity_uses_provided_activity(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        client = AgentClient(sender, collector)
        
        original_activity = Activity(type=ActivityTypes.typing)
        result = client.activity(original_activity)
        
        assert result.type == ActivityTypes.typing

    def test_activity_applies_template_defaults(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        template = ActivityTemplate({"channel_id": "test-channel"})
        client = AgentClient(sender, collector, activity_template=template)
        
        result = client.activity("hello")
        
        assert result.channel_id == "test-channel"

    def test_activity_preserves_activity_values_over_template(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        template = ActivityTemplate({"text": "default text", "channel_id": "test-channel"})
        client = AgentClient(sender, collector, activity_template=template)
        
        result = client.activity("custom text")
        
        assert result.text == "custom text"
        assert result.channel_id == "test-channel"


class TestAgentClientGetActivities:
    """Test AgentClient.get_activities method."""

    def test_get_activities_returns_collector_activities(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        activities = [Activity(type="message", text="test")]
        collector.get_activities.return_value = activities
        
        client = AgentClient(sender, collector)
        result = client.get_activities()
        
        assert result == activities
        collector.get_activities.assert_called_once()


class TestAgentClientGetInvokeResponses:
    """Test AgentClient.get_invoke_responses method."""

    def test_get_invoke_responses_returns_collector_invoke_responses(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        responses = [InvokeResponse(status=200)]
        collector.get_invoke_responses.return_value = responses
        
        client = AgentClient(sender, collector)
        result = client.get_invoke_responses()
        
        assert result == responses
        collector.get_invoke_responses.assert_called_once()


class TestAgentClientSend:
    """Test AgentClient.send method."""

    @pytest.mark.asyncio
    async def test_send_pops_collector_before_sending(self):
        sender = MagicMock(spec=SenderClient)
        sender.send = AsyncMock(return_value="")
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        await client.send("hello")
        
        assert collector.pop.call_count == 2  # Once at start, once at end

    @pytest.mark.asyncio
    async def test_send_string_creates_message_activity(self):
        sender = MagicMock(spec=SenderClient)
        sender.send = AsyncMock(return_value="")
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        await client.send("hello world")
        
        sender.send.assert_called_once()
        sent_activity = sender.send.call_args[0][0]
        assert sent_activity.type == ActivityTypes.message
        assert sent_activity.text == "hello world"

    @pytest.mark.asyncio
    async def test_send_invoke_activity_calls_send_invoke(self):
        sender = MagicMock(spec=SenderClient)
        invoke_response = InvokeResponse(status=200)
        sender.send_invoke = AsyncMock(return_value=invoke_response)
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        invoke_activity = Activity(type=ActivityTypes.invoke, name="test")
        await client.send(invoke_activity)
        
        sender.send_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_invoke_adds_response_to_collector(self):
        sender = MagicMock(spec=SenderClient)
        invoke_response = InvokeResponse(status=200)
        sender.send_invoke = AsyncMock(return_value=invoke_response)
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        invoke_activity = Activity(type=ActivityTypes.invoke, name="test")
        await client.send(invoke_activity)
        
        collector.add.assert_called_once_with(invoke_response)

    @pytest.mark.asyncio
    async def test_send_expect_replies_activity_calls_send_expect_replies(self):
        sender = MagicMock(spec=SenderClient)
        replies = [Activity(type="message", text="reply")]
        sender.send_expect_replies = AsyncMock(return_value=replies)
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        activity = Activity(type=ActivityTypes.message, delivery_mode=DeliveryModes.expect_replies)
        await client.send(activity)
        
        sender.send_expect_replies.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_expect_replies_adds_replies_to_collector(self):
        sender = MagicMock(spec=SenderClient)
        reply1 = Activity(type="message", text="reply1")
        reply2 = Activity(type="message", text="reply2")
        sender.send_expect_replies = AsyncMock(return_value=[reply1, reply2])
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        activity = Activity(type=ActivityTypes.message, delivery_mode=DeliveryModes.expect_replies)
        await client.send(activity)
        
        assert collector.add.call_count == 2
        collector.add.assert_any_call(reply1)
        collector.add.assert_any_call(reply2)

    @pytest.mark.asyncio
    async def test_send_expect_replies_returns_received_activities(self):
        sender = MagicMock(spec=SenderClient)
        reply = Activity(type="message", text="reply")
        sender.send_expect_replies = AsyncMock(return_value=[reply])
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        activity = Activity(type=ActivityTypes.message, delivery_mode=DeliveryModes.expect_replies)
        result = await client.send(activity)
        
        assert reply in result

    @pytest.mark.asyncio
    async def test_send_regular_activity_calls_sender_send(self):
        sender = MagicMock(spec=SenderClient)
        sender.send = AsyncMock(return_value="")
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        await client.send("hello")
        
        sender.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_response_wait_waits_before_returning(self):
        sender = MagicMock(spec=SenderClient)
        sender.send = AsyncMock(return_value="")
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        
        import time
        start = time.time()
        await client.send("hello", response_wait=0.1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_send_returns_combined_activities(self):
        sender = MagicMock(spec=SenderClient)
        reply = Activity(type="message", text="immediate reply")
        sender.send_expect_replies = AsyncMock(return_value=[reply])
        collector = MagicMock(spec=ResponseCollector)
        post_activity = Activity(type="message", text="post activity")
        collector.pop.return_value = [post_activity]
        
        client = AgentClient(sender, collector)
        activity = Activity(type=ActivityTypes.message, delivery_mode=DeliveryModes.expect_replies)
        result = await client.send(activity)
        
        assert reply in result
        assert post_activity in result

    @pytest.mark.asyncio
    async def test_send_zero_response_wait_does_not_delay(self):
        sender = MagicMock(spec=SenderClient)
        sender.send = AsyncMock(return_value="")
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        
        import time
        start = time.time()
        await client.send("hello", response_wait=0.0)
        elapsed = time.time() - start
        
        # Should complete very quickly without delay
        assert elapsed < 0.1


class TestAgentClientSendExpectReplies:
    """Test AgentClient.send_expect_replies method."""

    @pytest.mark.asyncio
    async def test_send_expect_replies_sets_delivery_mode(self):
        sender = MagicMock(spec=SenderClient)
        sender.send_expect_replies = AsyncMock(return_value=[])
        collector = MagicMock(spec=ResponseCollector)
        
        client = AgentClient(sender, collector)
        await client.send_expect_replies("hello")
        
        sent_activity = sender.send_expect_replies.call_args[0][0]
        assert sent_activity.delivery_mode == DeliveryModes.expect_replies

    @pytest.mark.asyncio
    async def test_send_expect_replies_calls_sender_send_expect_replies(self):
        sender = MagicMock(spec=SenderClient)
        sender.send_expect_replies = AsyncMock(return_value=[])
        collector = MagicMock(spec=ResponseCollector)
        
        client = AgentClient(sender, collector)
        await client.send_expect_replies("hello")
        
        sender.send_expect_replies.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_expect_replies_adds_activities_to_collector(self):
        sender = MagicMock(spec=SenderClient)
        reply1 = Activity(type="message", text="reply1")
        reply2 = Activity(type="message", text="reply2")
        sender.send_expect_replies = AsyncMock(return_value=[reply1, reply2])
        collector = MagicMock(spec=ResponseCollector)
        
        client = AgentClient(sender, collector)
        await client.send_expect_replies("hello")
        
        assert collector.add.call_count == 2
        collector.add.assert_any_call(reply1)
        collector.add.assert_any_call(reply2)

    @pytest.mark.asyncio
    async def test_send_expect_replies_returns_activities(self):
        sender = MagicMock(spec=SenderClient)
        reply = Activity(type="message", text="reply")
        sender.send_expect_replies = AsyncMock(return_value=[reply])
        collector = MagicMock(spec=ResponseCollector)
        
        client = AgentClient(sender, collector)
        result = await client.send_expect_replies("hello")
        
        assert result == [reply]

    @pytest.mark.asyncio
    async def test_send_expect_replies_with_activity_object(self):
        sender = MagicMock(spec=SenderClient)
        sender.send_expect_replies = AsyncMock(return_value=[])
        collector = MagicMock(spec=ResponseCollector)
        
        client = AgentClient(sender, collector)
        original_activity = Activity(type=ActivityTypes.message, text="test")
        await client.send_expect_replies(original_activity)
        
        sent_activity = sender.send_expect_replies.call_args[0][0]
        assert sent_activity.text == "test"
        assert sent_activity.delivery_mode == DeliveryModes.expect_replies


class TestAgentClientWaitForResponses:
    """Test AgentClient.wait_for_responses method."""

    @pytest.mark.asyncio
    async def test_wait_for_responses_returns_popped_activities(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        activities = [Activity(type="message", text="response")]
        collector.pop.return_value = activities
        
        client = AgentClient(sender, collector)
        result = await client.wait_for_responses()
        
        assert result == activities

    @pytest.mark.asyncio
    async def test_wait_for_responses_waits_for_duration(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        
        import time
        start = time.time()
        await client.wait_for_responses(duration=0.1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_wait_for_responses_zero_duration_returns_immediately(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        
        import time
        start = time.time()
        await client.wait_for_responses(duration=0.0)
        elapsed = time.time() - start
        
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_wait_for_responses_raises_on_negative_duration(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        
        client = AgentClient(sender, collector)
        
        with pytest.raises(ValueError, match="Duration must be non-negative"):
            await client.wait_for_responses(duration=-1.0)

    @pytest.mark.asyncio
    async def test_wait_for_responses_calls_pop_after_waiting(self):
        sender = MagicMock(spec=SenderClient)
        collector = MagicMock(spec=ResponseCollector)
        collector.pop.return_value = []
        
        client = AgentClient(sender, collector)
        await client.wait_for_responses(duration=0.01)
        
        collector.pop.assert_called_once()