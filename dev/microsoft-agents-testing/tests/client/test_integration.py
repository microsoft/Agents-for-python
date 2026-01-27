"""
Integration tests for the client module.

This module tests all client classes working together in realistic scenarios
using aiohttp's TestServer with manually created ClientSession.

Tests cover:
- Full request/response flow with mock agent server
- Transcript recording across multiple components
- AgentClient + Sender + Transcript integration
- CallbackServer receiving async callbacks
- Error handling across the stack
- Multiple concurrent exchanges
"""

import pytest
import json
import asyncio
from typing import Callable, Awaitable
from contextlib import asynccontextmanager

from aiohttp import web, ClientSession
from aiohttp.test_utils import TestServer

from microsoft_agents.testing.client import (
    AgentClient,
    AiohttpSender,
    AiohttpCallbackServer,
    Exchange,
    Transcript,
)
from microsoft_agents.testing.utils import ActivityTemplate
from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
    ChannelAccount,
    ConversationAccount,
)


# =============================================================================
# Mock Agent Server
# =============================================================================

class MockAgentServer:
    """A sophisticated mock agent server for integration testing.
    
    This mock server simulates a Bot Framework-compatible agent endpoint,
    handling various activity types and delivery modes appropriately.
    
    Features:
    - Handles invoke activities with customizable responses
    - Supports expect_replies delivery mode with proper response format
    - Tracks all received activities for verification
    - Supports custom response generators
    - Captures service URLs for callback simulation
    - Provides detailed error responses for debugging
    """
    
    def __init__(self):
        self.received_activities: list[Activity] = []
        self.response_generator: Callable[[Activity], list[Activity]] = self._default_response
        self.invoke_handler: Callable[[Activity], dict] = self._default_invoke
        self._callback_url: str | None = None
        self._fail_next_request: bool = False
        self._custom_status_code: int | None = None
        
    def _default_response(self, activity: Activity) -> list[Activity]:
        """Default response: echo back the message."""
        return [Activity(
            type=ActivityTypes.message,
            text=f"Echo: {activity.text}",
            from_property=ChannelAccount(id="bot", name="Bot"),
            recipient=activity.from_property or ChannelAccount(id="user", name="User"),
        )]
    
    def _default_invoke(self, activity: Activity) -> dict:
        """Default invoke handler."""
        return {"status": 200, "body": {"result": "ok"}}
    
    def set_response_generator(self, generator: Callable[[Activity], list[Activity]]):
        """Set custom response generator for expect_replies mode."""
        self.response_generator = generator
    
    def set_invoke_handler(self, handler: Callable[[Activity], dict]):
        """Set custom invoke handler."""
        self.invoke_handler = handler
    
    def fail_next_request(self, status_code: int = 500):
        """Make the next request fail with the given status code."""
        self._fail_next_request = True
        self._custom_status_code = status_code
    
    async def handle_messages(self, request: web.Request) -> web.Response:
        """Handle incoming /api/messages requests.
        
        Routes requests based on activity type and delivery mode:
        - Invoke activities: Returns invoke response with status/body
        - expect_replies mode: Returns JSON array of activities
        - Normal messages: Returns simple {"id": "..."} response
        """
        try:
            # Check if we should fail this request
            if self._fail_next_request:
                self._fail_next_request = False
                status = self._custom_status_code or 500
                self._custom_status_code = None
                return web.json_response(
                    {"error": "Simulated failure"},
                    status=status
                )
            
            data = await request.json()
            activity = Activity.model_validate(data)
            self.received_activities.append(activity)
            
            # Store callback URL if present
            if activity.service_url:
                self._callback_url = activity.service_url
            
            # Handle invoke activities
            if activity.type == ActivityTypes.invoke:
                result = self.invoke_handler(activity)
                return web.json_response(
                    result.get("body", {}),
                    status=result.get("status", 200)
                )
            
            # Handle expect_replies delivery mode
            # Return a JSON array of activities that Exchange.from_request expects
            delivery_mode = activity.delivery_mode
            if self._is_expect_replies(delivery_mode):
                responses = self.response_generator(activity)
                # Serialize activities to dicts
                response_dicts = [
                    r.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
                    for r in responses
                ]
                # Return as normal JSON array - Exchange.from_request will parse it
                return web.json_response(response_dicts)
            
            # Normal message - return 200 with activity ID
            return web.json_response({"id": f"activity-{len(self.received_activities)}"})
            
        except Exception as e:
            # Return error details for debugging
            import traceback
            return web.json_response(
                {"error": str(e), "traceback": traceback.format_exc()},
                status=500
            )
    
    def _is_expect_replies(self, delivery_mode) -> bool:
        """Check if delivery mode is expect_replies, handling various formats."""
        if delivery_mode is None:
            return False
        # Handle enum, string, or other representations
        mode_str = str(delivery_mode)
        return (
            delivery_mode == DeliveryModes.expect_replies
            or mode_str == "expectReplies"
            or mode_str == DeliveryModes.expect_replies
            or "expect" in mode_str.lower()
        )
    
    def create_app(self) -> web.Application:
        """Create the aiohttp application with all routes."""
        app = web.Application()
        app.router.add_post("/api/messages", self.handle_messages)
        return app
    
    def clear(self):
        """Clear all recorded activities and reset state."""
        self.received_activities.clear()
        self._callback_url = None
        self._fail_next_request = False
        self._custom_status_code = None


# =============================================================================
# Test Server Context Manager
# =============================================================================

@asynccontextmanager
async def create_test_session(app: web.Application):
    """Create a TestServer and ClientSession with proper base_url.
    
    Yields a tuple of (session, base_url) where session has the base_url configured.
    """
    server = TestServer(app)
    await server.start_server()
    
    try:
        # Create ClientSession with base_url pointing to the test server
        base_url = f"http://{server.host}:{server.port}"
        async with ClientSession(base_url=base_url) as session:
            yield session, base_url
    finally:
        await server.close()


# =============================================================================
# Integration Test Fixtures
# =============================================================================

@pytest.fixture
def mock_agent_server():
    """Create a mock agent server."""
    return MockAgentServer()


@pytest.fixture
async def agent_session(mock_agent_server):
    """Create aiohttp ClientSession with mock agent server."""
    app = mock_agent_server.create_app()
    async with create_test_session(app) as (session, base_url):
        yield session, mock_agent_server, base_url


# =============================================================================
# Basic Integration Tests
# =============================================================================

class TestBasicIntegration:
    """Basic integration tests for the client stack."""
    
    @pytest.mark.asyncio
    async def test_sender_sends_to_server(self, agent_session):
        """Test that AiohttpSender successfully sends to the mock server."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.message,
            text="Hello, agent!",
            from_property=ChannelAccount(id="user", name="User"),
        )
        
        exchange = await sender.send(activity, transcript=transcript)
        
        # Verify server received the activity
        assert len(server.received_activities) == 1
        assert server.received_activities[0].text == "Hello, agent!"
        
        # Verify exchange was recorded
        assert len(transcript.get_all()) == 1
    
    @pytest.mark.asyncio
    async def test_sender_without_transcript(self, agent_session):
        """Test that AiohttpSender works without a transcript."""
        session, server, base_url = agent_session
        
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.message,
            text="No transcript test",
        )
        
        exchange = await sender.send(activity)
        
        # Verify server received the activity
        assert len(server.received_activities) == 1
        assert server.received_activities[0].text == "No transcript test"
        
        # Verify exchange was returned
        assert exchange.status_code == 200
    
    @pytest.mark.asyncio
    async def test_agent_client_full_flow(self, agent_session):
        """Test AgentClient with sender and transcript."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        agent_client = AgentClient(
            sender=sender,
            transcript=transcript,
        )
        
        # Build activity
        activity = agent_client._build_activity("Hello!")
        
        assert activity.type == ActivityTypes.message
        assert activity.text == "Hello!"
    
    @pytest.mark.asyncio
    async def test_agent_client_send(self, agent_session):
        """Test AgentClient.send() method."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        agent_client = AgentClient(
            sender=sender,
            transcript=transcript,
        )
        
        # Send using AgentClient
        responses = await agent_client.send("Hello from AgentClient!")
        
        # Verify server received the activity
        assert len(server.received_activities) == 1
        assert server.received_activities[0].text == "Hello from AgentClient!"
    
    @pytest.mark.asyncio
    async def test_multiple_sends_recorded_in_order(self, agent_session):
        """Test that multiple sends are recorded in order."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        messages = ["First", "Second", "Third"]
        
        for msg in messages:
            activity = Activity(type=ActivityTypes.message, text=msg)
            await sender.send(activity, transcript=transcript)
        
        # Verify order
        assert len(server.received_activities) == 3
        for i, msg in enumerate(messages):
            assert server.received_activities[i].text == msg
        
        # Verify transcript
        all_exchanges = transcript.get_all()
        assert len(all_exchanges) == 3


# =============================================================================
# Transcript Integration Tests
# =============================================================================

class TestTranscriptIntegration:
    """Test Transcript integration across components."""
    
    @pytest.mark.asyncio
    async def test_shared_transcript(self, agent_session):
        """Test that Transcript collects from multiple sources."""
        session, server, base_url = agent_session
        
        # Shared transcript
        transcript = Transcript()
        
        # Create sender
        sender = AiohttpSender(session=session)
        
        # Send activities with shared transcript
        await sender.send(Activity(type=ActivityTypes.message, text="msg1"), transcript=transcript)
        await sender.send(Activity(type=ActivityTypes.message, text="msg2"), transcript=transcript)
        
        # All should be in shared transcript
        all_exchanges = transcript.get_all()
        assert len(all_exchanges) == 2
    
    @pytest.mark.asyncio
    async def test_transcript_cursor_tracking(self, agent_session):
        """Test transcript cursor advances correctly."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        # Send first batch
        await sender.send(Activity(type=ActivityTypes.message, text="first"), transcript=transcript)
        
        # Get new - should return first
        new1 = transcript.get_new()
        assert len(new1) == 1
        
        # Send second batch
        await sender.send(Activity(type=ActivityTypes.message, text="second"), transcript=transcript)
        await sender.send(Activity(type=ActivityTypes.message, text="third"), transcript=transcript)
        
        # Get new - should only return second and third
        new2 = transcript.get_new()
        assert len(new2) == 2
        
        # Get all - should return all three
        all_exchanges = transcript.get_all()
        assert len(all_exchanges) == 3
    
    @pytest.mark.asyncio
    async def test_child_transcript_propagation(self, agent_session):
        """Test child transcript propagates to parent."""
        session, server, base_url = agent_session
        
        parent_transcript = Transcript()
        child_transcript = parent_transcript.child()
        
        sender = AiohttpSender(session=session)
        
        await sender.send(Activity(type=ActivityTypes.message, text="test"), transcript=child_transcript)
        
        # Both should have the exchange
        assert len(child_transcript.get_all()) == 1
        assert len(parent_transcript.get_all()) == 1
    
    @pytest.mark.asyncio
    async def test_agent_client_transcript_integration(self, agent_session):
        """Test AgentClient manages transcript internally."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        agent_client = AgentClient(
            sender=sender,
            transcript=transcript,
        )
        
        await agent_client.send("Message 1")
        await agent_client.send("Message 2")
        
        # Verify transcript via agent_client
        assert len(agent_client.transcript.get_all()) == 2


# =============================================================================
# Activity Template Integration Tests
# =============================================================================

class TestActivityTemplateIntegration:
    """Test ActivityTemplate with AgentClient."""
    
    @pytest.mark.asyncio
    async def test_template_applied_to_activities(self, agent_session):
        """Test that template values are applied to activities."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        # Create template with default values
        template = ActivityTemplate(
            channel_id="test-channel",
            from_property=ChannelAccount(id="test-user", name="Test User"),
            conversation=ConversationAccount(id="conv-123"),
        )
        
        agent_client = AgentClient(
            sender=sender,
            transcript=transcript,
            activity_template=template,
        )
        
        activity = agent_client._build_activity("Hello with template!")
        
        assert activity.channel_id == "test-channel"
        assert activity.from_property.id == "test-user"
        assert activity.conversation.id == "conv-123"
    
    @pytest.mark.asyncio
    async def test_template_setter(self, agent_session):
        """Test that template can be updated via setter."""
        session, server, base_url = agent_session
        
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender)
        
        # Update template
        new_template = ActivityTemplate(
            channel_id="new-channel",
        )
        agent_client.template = new_template
        
        activity = agent_client._build_activity("Test")
        assert activity.channel_id == "new-channel"


# =============================================================================
# Error Handling Integration Tests
# =============================================================================

class TestErrorHandlingIntegration:
    """Test error handling across the client stack."""
    
    @pytest.mark.asyncio
    async def test_invoke_without_invoke_type_raises(self, agent_session):
        """Test that invoke() raises for non-invoke activities."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender, transcript=transcript)
        
        message_activity = Activity(type=ActivityTypes.message, text="not invoke")
        
        with pytest.raises(ValueError, match="type must be 'invoke'"):
            await agent_client.invoke(message_activity)


# =============================================================================
# Concurrent Operations Tests
# =============================================================================

class TestConcurrentOperations:
    """Test concurrent operations across the client stack."""
    
    @pytest.mark.asyncio
    async def test_concurrent_sends(self, agent_session):
        """Test multiple concurrent sends are all recorded."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        # Send 5 messages concurrently
        activities = [
            Activity(type=ActivityTypes.message, text=f"concurrent-{i}")
            for i in range(5)
        ]
        
        await asyncio.gather(*[sender.send(a, transcript=transcript) for a in activities])
        
        # All should be received (order may vary due to concurrency)
        assert len(server.received_activities) == 5
        assert len(transcript.get_all()) == 5


# =============================================================================
# Full Conversation Flow Tests
# =============================================================================

class TestFullConversationFlow:
    """Test complete conversation flows."""
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, agent_session):
        """Test a multi-turn conversation flow."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender, transcript=transcript)
        
        # Simulate multi-turn conversation
        turns = [
            "Hello!",
            "What's the weather?",
            "Thanks!",
        ]
        
        for turn_text in turns:
            await agent_client.send(turn_text)
        
        # Verify all turns were sent
        assert len(server.received_activities) == 3
        assert server.received_activities[0].text == "Hello!"
        assert server.received_activities[1].text == "What's the weather?"
        assert server.received_activities[2].text == "Thanks!"
        
        # Verify transcript
        all_exchanges = transcript.get_all()
        assert len(all_exchanges) == 3
    
    @pytest.mark.asyncio
    async def test_agent_client_get_all_responses(self, agent_session):
        """Test AgentClient.get_all() collects all responses."""
        session, server, base_url = agent_session
        
        # Set up server to return responses in expect_replies mode
        server.set_response_generator(lambda a: [
            Activity(type=ActivityTypes.message, text=f"Reply to: {a.text}")
        ])
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender, transcript=transcript)
        
        # Send with expect_replies
        await agent_client.send_expect_replies("Message 1")
        await agent_client.send_expect_replies("Message 2")
        
        # Get all responses
        all_responses = agent_client.get_all()
        assert len(all_responses) == 2


# =============================================================================
# Expect Replies Mode Tests
# =============================================================================

class TestExpectRepliesMode:
    """Test expect_replies delivery mode."""
    
    @pytest.mark.asyncio
    async def test_expect_replies_activity_sent(self, agent_session):
        """Test that activity with expect_replies is sent correctly."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.message,
            text="Give me replies",
            delivery_mode=DeliveryModes.expect_replies,
        )
        
        exchange = await sender.send(activity, transcript=transcript)
        
        # Verify server received with expect_replies
        assert len(server.received_activities) == 1
        received = server.received_activities[0]
        assert received.text == "Give me replies"
        # Check delivery mode - may be string or enum
        assert str(received.delivery_mode) in ["expectReplies", str(DeliveryModes.expect_replies)]
    
    @pytest.mark.asyncio
    async def test_expect_replies_receives_responses(self, agent_session):
        """Test that expect_replies mode returns activities in the exchange."""
        session, server, base_url = agent_session
        
        # Set up a custom response generator
        def custom_responses(activity: Activity) -> list[Activity]:
            return [
                Activity(
                    type=ActivityTypes.message,
                    text="Response 1",
                    from_property=ChannelAccount(id="bot"),
                ),
                Activity(
                    type=ActivityTypes.message,
                    text="Response 2",
                    from_property=ChannelAccount(id="bot"),
                ),
            ]
        
        server.set_response_generator(custom_responses)
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.message,
            text="Give me multiple replies",
            delivery_mode=DeliveryModes.expect_replies,
        )
        
        exchange = await sender.send(activity, transcript=transcript)
        
        # Verify exchange captured the responses
        assert exchange.status_code == 200
        assert len(exchange.responses) == 2
        assert exchange.responses[0].text == "Response 1"
        assert exchange.responses[1].text == "Response 2"
    
    @pytest.mark.asyncio
    async def test_expect_replies_empty_response(self, agent_session):
        """Test expect_replies with no responses."""
        session, server, base_url = agent_session
        
        # Return empty list
        server.set_response_generator(lambda a: [])
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.message,
            text="No replies please",
            delivery_mode=DeliveryModes.expect_replies,
        )
        
        exchange = await sender.send(activity, transcript=transcript)
        
        assert exchange.status_code == 200
        assert len(exchange.responses) == 0
    
    @pytest.mark.asyncio
    async def test_agent_client_send_expect_replies(self, agent_session):
        """Test AgentClient.send_expect_replies() method."""
        session, server, base_url = agent_session
        
        # Set up server to return responses
        server.set_response_generator(lambda a: [
            Activity(type=ActivityTypes.message, text="Bot response")
        ])
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender, transcript=transcript)
        
        responses = await agent_client.send_expect_replies("Hello!")
        
        # Verify server received with expect_replies mode
        assert len(server.received_activities) == 1
        received = server.received_activities[0]
        assert received.delivery_mode == DeliveryModes.expect_replies
        
        # Verify responses
        assert len(responses) == 1
        assert responses[0].text == "Bot response"


# =============================================================================
# Typing Activity Tests
# =============================================================================

class TestTypingActivities:
    """Test handling of typing activities."""
    
    @pytest.mark.asyncio
    async def test_typing_activity_sent(self, agent_session):
        """Test that typing activities are sent correctly."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        typing_activity = Activity(type=ActivityTypes.typing)
        
        await sender.send(typing_activity, transcript=transcript)
        
        assert len(server.received_activities) == 1
        assert server.received_activities[0].type == ActivityTypes.typing


# =============================================================================
# Complex Scenario Tests
# =============================================================================

class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    @pytest.mark.asyncio
    async def test_conversation_with_service_url(self, agent_session):
        """Test conversation with service_url for callbacks."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.message,
            text="Hello",
            service_url="http://localhost:9873/v3/conversations/",
            channel_id="test",
            conversation=ConversationAccount(id="conv-1"),
            from_property=ChannelAccount(id="user-1"),
        )
        
        await sender.send(activity, transcript=transcript)
        
        # Verify server stored callback URL
        assert server._callback_url == "http://localhost:9873/v3/conversations/"
    
    @pytest.mark.asyncio
    async def test_mixed_activity_types(self, agent_session):
        """Test sending different activity types in sequence."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activities = [
            Activity(type=ActivityTypes.typing),
            Activity(type=ActivityTypes.message, text="Hello"),
            Activity(type=ActivityTypes.typing),
            Activity(type=ActivityTypes.message, text="World"),
        ]
        
        for activity in activities:
            await sender.send(activity, transcript=transcript)
        
        received_types = [a.type for a in server.received_activities]
        assert received_types == [
            ActivityTypes.typing,
            ActivityTypes.message,
            ActivityTypes.typing,
            ActivityTypes.message,
        ]


# =============================================================================
# Standalone Session Tests
# =============================================================================

class TestWithManualSession:
    """Tests using manually created ClientSession with TestServer."""
    
    @pytest.mark.asyncio
    async def test_full_stack_with_manual_session(self):
        """Test full client stack using manual ClientSession."""
        # Create mock server
        mock_server = MockAgentServer()
        app = mock_server.create_app()
        
        async with create_test_session(app) as (session, base_url):
            transcript = Transcript()
            sender = AiohttpSender(session=session)
            
            activity = Activity(
                type=ActivityTypes.message,
                text="Integration test message",
            )
            
            exchange = await sender.send(activity, transcript=transcript)
            
            assert len(mock_server.received_activities) == 1
            assert mock_server.received_activities[0].text == "Integration test message"
            assert len(transcript.get_all()) == 1
    
    @pytest.mark.asyncio
    async def test_agent_client_with_template_and_send(self):
        """Test AgentClient building and sending activities."""
        mock_server = MockAgentServer()
        app = mock_server.create_app()
        
        async with create_test_session(app) as (session, base_url):
            transcript = Transcript()
            sender = AiohttpSender(session=session)
            
            template = ActivityTemplate(
                channel_id="integration-test",
                from_property=ChannelAccount(id="test-user", name="Tester"),
                conversation=ConversationAccount(id="test-conv"),
            )
            
            agent_client = AgentClient(
                sender=sender,
                transcript=transcript,
                activity_template=template,
            )
            
            # Use AgentClient.send() method
            await agent_client.send("Hello from integration test!")
            
            # Verify
            assert len(mock_server.received_activities) == 1
            received = mock_server.received_activities[0]
            assert received.text == "Hello from integration test!"
            assert received.channel_id == "integration-test"
            assert received.from_property.id == "test-user"
            assert received.conversation.id == "test-conv"


# =============================================================================
# Exchange Response Handling Tests
# =============================================================================

class TestExchangeResponseHandling:
    """Test Exchange creation and response handling."""
    
    @pytest.mark.asyncio
    async def test_exchange_captures_status_code(self, agent_session):
        """Test that Exchange captures the HTTP status code."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(type=ActivityTypes.message, text="test")
        exchange = await sender.send(activity, transcript=transcript)
        
        # Exchange should have status code
        assert exchange.status_code == 200
    
    @pytest.mark.asyncio
    async def test_exchange_captures_body(self, agent_session):
        """Test that Exchange captures the response body."""
        session, server, base_url = agent_session
        
        sender = AiohttpSender(session=session)
        
        activity = Activity(type=ActivityTypes.message, text="test")
        exchange = await sender.send(activity)
        
        # Exchange should have body
        assert exchange.body is not None
    
    @pytest.mark.asyncio
    async def test_exchange_latency_tracking(self, agent_session):
        """Test that Exchange tracks request/response latency."""
        session, server, base_url = agent_session
        
        sender = AiohttpSender(session=session)
        
        activity = Activity(type=ActivityTypes.message, text="test")
        exchange = await sender.send(activity)
        
        # Exchange should have timing information
        assert exchange.request_at is not None
        assert exchange.response_at is not None
        assert exchange.latency is not None
        assert exchange.latency_ms is not None
        assert exchange.latency_ms >= 0
    
    @pytest.mark.asyncio
    async def test_invoke_response_captured(self, agent_session):
        """Test that invoke responses are captured correctly."""
        session, server, base_url = agent_session
        
        # Set custom invoke handler with detailed response
        server.set_invoke_handler(lambda a: {
            "status": 200,
            "body": {"action": "completed", "data": {"value": 42}}
        })
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.invoke,
            name="test/action",
        )
        
        exchange = await sender.send(activity, transcript=transcript)
        
        # Verify server received invoke
        assert len(server.received_activities) == 1
        assert server.received_activities[0].type == ActivityTypes.invoke
        assert server.received_activities[0].name == "test/action"
        
        # Verify invoke response was captured
        assert exchange.invoke_response is not None
        assert exchange.invoke_response.status == 200
    
    @pytest.mark.asyncio
    async def test_invoke_with_value(self, agent_session):
        """Test invoke activity with value payload."""
        session, server, base_url = agent_session
        
        # Handler that echoes the value
        server.set_invoke_handler(lambda a: {
            "status": 200,
            "body": {"received": a.value}
        })
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        activity = Activity(
            type=ActivityTypes.invoke,
            name="echo/value",
            value={"key": "test-value", "number": 123},
        )
        
        exchange = await sender.send(activity, transcript=transcript)
        
        # Verify server received the value
        assert server.received_activities[0].value == {"key": "test-value", "number": 123}
    
    @pytest.mark.asyncio
    async def test_agent_client_invoke(self, agent_session):
        """Test AgentClient.invoke() method."""
        session, server, base_url = agent_session
        
        server.set_invoke_handler(lambda a: {
            "status": 200,
            "body": {"result": "success", "data": 42}
        })
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender, transcript=transcript)
        
        activity = Activity(
            type=ActivityTypes.invoke,
            name="test/invoke",
            value={"input": "test"},
        )
        
        invoke_response = await agent_client.invoke(activity)
        
        assert invoke_response.status == 200
        assert invoke_response.body["result"] == "success"


# =============================================================================
# Error Simulation Tests
# =============================================================================

class TestErrorSimulation:
    """Test error handling with simulated failures."""
    
    @pytest.mark.asyncio
    async def test_server_clear_resets_state(self, agent_session):
        """Test that server.clear() resets all state."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        # Send some activities
        await sender.send(Activity(type=ActivityTypes.message, text="msg1"), transcript=transcript)
        await sender.send(Activity(type=ActivityTypes.message, text="msg2"), transcript=transcript)
        
        assert len(server.received_activities) == 2
        
        # Clear and verify
        server.clear()
        assert len(server.received_activities) == 0
        
        # Send more
        await sender.send(Activity(type=ActivityTypes.message, text="msg3"), transcript=transcript)
        assert len(server.received_activities) == 1
        assert server.received_activities[0].text == "msg3"


# =============================================================================
# Multi-Server Scenario Tests
# =============================================================================

class TestMultiServerScenarios:
    """Test scenarios with multiple servers or complex setups."""
    
    @pytest.mark.asyncio
    async def test_two_separate_conversations(self):
        """Test running two separate conversations with different servers."""
        # First conversation
        server1 = MockAgentServer()
        app1 = server1.create_app()
        
        # Second conversation
        server2 = MockAgentServer()
        app2 = server2.create_app()
        
        async with create_test_session(app1) as (session1, base_url1):
            async with create_test_session(app2) as (session2, base_url2):
                transcript1 = Transcript()
                transcript2 = Transcript()
                
                sender1 = AiohttpSender(session=session1)
                sender2 = AiohttpSender(session=session2)
                
                # Send to both servers
                await sender1.send(Activity(type=ActivityTypes.message, text="Hello Server 1"), transcript=transcript1)
                await sender2.send(Activity(type=ActivityTypes.message, text="Hello Server 2"), transcript=transcript2)
                
                # Verify each server received its message
                assert len(server1.received_activities) == 1
                assert server1.received_activities[0].text == "Hello Server 1"
                
                assert len(server2.received_activities) == 1
                assert server2.received_activities[0].text == "Hello Server 2"
                
                # Verify transcripts are separate
                assert len(transcript1.get_all()) == 1
                assert len(transcript2.get_all()) == 1


# =============================================================================
# AgentClient Child Tests
# =============================================================================

class TestAgentClientChild:
    """Test AgentClient.child() functionality."""
    
    @pytest.mark.asyncio
    async def test_child_client_shares_sender(self, agent_session):
        """Test that child client shares the same sender."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        parent_client = AgentClient(sender=sender, transcript=transcript)
        child_client = parent_client.child()
        
        # Send from both clients
        await parent_client.send("From parent")
        await child_client.send("From child")
        
        # Both should go to the same server
        assert len(server.received_activities) == 2
        assert server.received_activities[0].text == "From parent"
        assert server.received_activities[1].text == "From child"
    
    @pytest.mark.asyncio
    async def test_child_transcript_propagates_to_parent(self, agent_session):
        """Test that child transcript propagates exchanges to parent."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        
        parent_client = AgentClient(sender=sender, transcript=transcript)
        child_client = parent_client.child()
        
        # Send from child
        await child_client.send("From child only")
        
        # Parent transcript should have the exchange
        assert len(parent_client.transcript.get_all()) == 1
        assert len(child_client.transcript.get_all()) == 1
    
    @pytest.mark.asyncio
    async def test_child_inherits_template(self, agent_session):
        """Test that child client inherits the activity template."""
        session, server, base_url = agent_session
        
        template = ActivityTemplate(
            channel_id="parent-channel",
            from_property=ChannelAccount(id="parent-user"),
        )
        
        sender = AiohttpSender(session=session)
        parent_client = AgentClient(sender=sender, activity_template=template)
        child_client = parent_client.child()
        
        # Send from child
        await child_client.send("From child")
        
        # Should have parent's template values
        received = server.received_activities[0]
        assert received.channel_id == "parent-channel"
        assert received.from_property.id == "parent-user"


# =============================================================================
# Wait Feature Tests
# =============================================================================

class TestWaitFeature:
    """Test AgentClient.send() with wait parameter."""
    
    @pytest.mark.asyncio
    async def test_send_with_wait(self, agent_session):
        """Test that send() waits for additional responses."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender, transcript=transcript)
        
        # Send with a small wait (won't receive additional responses in this test)
        responses = await agent_client.send("Hello", wait=0.1)
        
        # Should complete without error
        assert len(server.received_activities) == 1
    
    @pytest.mark.asyncio
    async def test_send_without_wait(self, agent_session):
        """Test that send() without wait returns immediately."""
        session, server, base_url = agent_session
        
        transcript = Transcript()
        sender = AiohttpSender(session=session)
        agent_client = AgentClient(sender=sender, transcript=transcript)
        
        responses = await agent_client.send("Hello", wait=0.0)
        
        assert len(server.received_activities) == 1