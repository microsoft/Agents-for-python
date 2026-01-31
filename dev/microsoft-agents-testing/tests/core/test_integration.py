# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Integration tests for ExternalScenario, AiohttpClientFactory, and related components.

These tests demonstrate the full HTTP-based testing infrastructure using:
- ExternalScenario
- AiohttpClientFactory
- AiohttpCallbackServer
- AiohttpSender
- AgentClient

Tests use a mock agent server created with aiohttp.test_utils to avoid
requiring external dependencies.
"""

import json
import pytest
from datetime import datetime
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from aiohttp import ClientSession
from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    DeliveryModes,
    InvokeResponse,
)

from microsoft_agents.testing.core.agent_client import AgentClient
from microsoft_agents.testing.core.aiohttp_client_factory import AiohttpClientFactory
from microsoft_agents.testing.core.client_config import ClientConfig
from microsoft_agents.testing.core.external_scenario import ExternalScenario
from microsoft_agents.testing.core.scenario import ScenarioConfig
from microsoft_agents.testing.core.fluent import (
    ActivityTemplate,
    Expect,
    Select,
)
from microsoft_agents.testing.core.transport import (
    Transcript,
    Exchange,
    AiohttpSender,
    AiohttpCallbackServer,
)


# ============================================================================
# Mock Agent Server - Simulates a real agent endpoint
# ============================================================================

class MockAgentServer:
    """A mock agent server for testing HTTP-based agent communication.
    
    This creates a real HTTP server that responds to agent protocol requests,
    allowing full end-to-end testing without external dependencies.
    """
    
    def __init__(self, port: int = 9999):
        self._port = port
        self._responses: dict[str, list[dict]] = {}
        self._invoke_responses: dict[str, dict] = {}
        self._default_response: list[dict] = []
        self._received_activities: list[Activity] = []
        self._app: Application = Application()
        self._app.router.add_post("/api/messages", self._handle_messages)
    
    def on_text(self, text: str, *responses: Activity) -> "MockAgentServer":
        """Configure responses for specific text."""
        self._responses[text.lower()] = [
            r.model_dump(by_alias=True, exclude_none=True, mode="json") 
            for r in responses
        ]
        return self
    
    def on_invoke(self, name: str, status: int, body: dict) -> "MockAgentServer":
        """Configure invoke response for specific action."""
        self._invoke_responses[name] = {"status": status, "body": body}
        return self
    
    def default_response(self, *responses: Activity) -> "MockAgentServer":
        """Set default response for unmatched messages."""
        self._default_response = [
            r.model_dump(by_alias=True, exclude_none=True, mode="json") 
            for r in responses
        ]
        return self
    
    @property
    def received_activities(self) -> list[Activity]:
        """Get all activities received by the server."""
        return self._received_activities
    
    @property
    def endpoint(self) -> str:
        """Get the server endpoint URL."""
        return f"http://localhost:{self._port}"
    
    async def _handle_messages(self, request: Request) -> Response:
        """Handle incoming agent messages."""
        try:
            data = await request.json()
            activity = Activity.model_validate(data)
            self._received_activities.append(activity)
            
            # Handle invoke activities
            if activity.type == ActivityTypes.invoke:
                if activity.name in self._invoke_responses:
                    resp = self._invoke_responses[activity.name]
                    return Response(
                        status=resp["status"],
                        content_type="application/json",
                        text=json.dumps(resp["body"])
                    )
                return Response(
                    status=200,
                    content_type="application/json",
                    text=json.dumps({"status": "ok"})
                )
            
            # Handle expect_replies
            if activity.delivery_mode == DeliveryModes.expect_replies:
                responses = self._get_responses(activity)
                return Response(
                    status=200,
                    content_type="application/json",
                    text=json.dumps(responses)
                )
            
            # Normal message - just acknowledge
            return Response(
                status=200,
                content_type="application/json",
                text=json.dumps({"id": "msg-1"})
            )
            
        except Exception as e:
            return Response(status=500, text=str(e))
    
    def _get_responses(self, activity: Activity) -> list[dict]:
        """Get configured responses for an activity."""
        if activity.text:
            text_lower = activity.text.lower()
            if text_lower in self._responses:
                return self._responses[text_lower]
        return self._default_response
    
    @asynccontextmanager
    async def run(self) -> AsyncIterator["MockAgentServer"]:
        """Start the mock server and yield self."""
        async with TestServer(self._app, host="localhost", port=self._port) as server:
            yield self


# ============================================================================
# AiohttpSender Integration Tests
# ============================================================================

class TestAiohttpSenderIntegration:
    """Integration tests for AiohttpSender with real HTTP."""

    @pytest.mark.asyncio
    async def test_sender_posts_to_real_server(self):
        """AiohttpSender posts to a real HTTP server."""
        mock_server = MockAgentServer(port=9901)
        mock_server.default_response(Activity(type=ActivityTypes.message, text="Reply"))
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                activity = Activity(type=ActivityTypes.message, text="Hello")
                
                exchange = await sender.send(activity)
                
                assert exchange.status_code == 200
                assert len(mock_server.received_activities) == 1
                assert mock_server.received_activities[0].text == "Hello"

    @pytest.mark.asyncio
    async def test_sender_with_expect_replies(self):
        """AiohttpSender handles expect_replies delivery mode."""
        mock_server = MockAgentServer(port=9902)
        mock_server.default_response(
            Activity(type=ActivityTypes.message, text="Reply 1"),
            Activity(type=ActivityTypes.message, text="Reply 2")
        )
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                activity = Activity(
                    type=ActivityTypes.message,
                    text="Hello",
                    delivery_mode=DeliveryModes.expect_replies
                )
                
                exchange = await sender.send(activity)
                
                assert len(exchange.responses) == 2
                assert exchange.responses[0].text == "Reply 1"
                assert exchange.responses[1].text == "Reply 2"

    @pytest.mark.asyncio
    async def test_sender_with_invoke(self):
        """AiohttpSender handles invoke activities."""
        mock_server = MockAgentServer(port=9903)
        mock_server.on_invoke("action/test", 200, {"result": "success"})
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                activity = Activity(type=ActivityTypes.invoke, name="action/test")
                
                exchange = await sender.send(activity)
                
                assert exchange.invoke_response is not None
                assert exchange.invoke_response.status == 200
                assert exchange.invoke_response.body == {"result": "success"}

    @pytest.mark.asyncio
    async def test_sender_records_to_transcript(self):
        """AiohttpSender records exchanges to transcript."""
        mock_server = MockAgentServer(port=9904)
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                transcript = Transcript()
                
                activity1 = Activity(type=ActivityTypes.message, text="First")
                activity2 = Activity(type=ActivityTypes.message, text="Second")
                
                await sender.send(activity1, transcript=transcript)
                await sender.send(activity2, transcript=transcript)
                
                assert len(transcript.history()) == 2
                assert transcript.history()[0].request.text == "First"
                assert transcript.history()[1].request.text == "Second"


# ============================================================================
# AgentClient with AiohttpSender Integration Tests
# ============================================================================

class TestAgentClientWithAiohttpSender:
    """Integration tests for AgentClient using AiohttpSender."""

    @pytest.mark.asyncio
    async def test_client_sends_via_http(self):
        """AgentClient sends activities via real HTTP."""
        mock_server = MockAgentServer(port=9905)
        mock_server.default_response(Activity(type=ActivityTypes.message, text="OK"))
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                template = ActivityTemplate(
                    channel_id="test",
                    **{"conversation.id": "conv-1", "from.id": "user-1"}
                )
                client = AgentClient(sender=sender, template=template)
                
                responses = await client.send_expect_replies("Hello")
                
                assert len(responses) == 1
                assert responses[0].text == "OK"
                
                # Verify server received properly formatted activity
                received = mock_server.received_activities[0]
                assert received.channel_id == "test"
                assert received.conversation.id == "conv-1"
                assert received.from_property.id == "user-1"

    @pytest.mark.asyncio
    async def test_client_full_conversation_flow(self):
        """AgentClient handles full conversation with multiple exchanges."""
        mock_server = MockAgentServer(port=9906)
        mock_server.on_text("hello", Activity(type=ActivityTypes.message, text="Hi there!"))
        mock_server.on_text("bye", Activity(type=ActivityTypes.message, text="Goodbye!"))
        mock_server.default_response(Activity(type=ActivityTypes.message, text="I don't understand"))
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                client = AgentClient(sender=sender)
                
                # Greeting
                response1 = await client.send_expect_replies("Hello")
                assert response1[0].text == "Hi there!"
                
                # Unknown
                response2 = await client.send_expect_replies("Random stuff")
                assert response2[0].text == "I don't understand"
                
                # Goodbye
                response3 = await client.send_expect_replies("Bye")
                assert response3[0].text == "Goodbye!"
                
                # Verify transcript
                assert len(client.ex_history()) == 3

    @pytest.mark.asyncio
    async def test_client_invoke_via_http(self):
        """AgentClient handles invoke activities via HTTP."""
        mock_server = MockAgentServer(port=9907)
        mock_server.on_invoke("submit/form", 200, {"submitted": True, "id": "form-123"})
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                client = AgentClient(sender=sender)
                
                invoke_response = await client.invoke(
                    Activity(type=ActivityTypes.invoke, name="submit/form", value={"data": "test"})
                )
                
                assert invoke_response.status == 200
                assert invoke_response.body["submitted"] is True
                assert invoke_response.body["id"] == "form-123"


# ============================================================================
# AiohttpCallbackServer Integration Tests
# ============================================================================

class TestAiohttpCallbackServerIntegration:
    """Integration tests for AiohttpCallbackServer."""

    @pytest.mark.asyncio
    async def test_callback_server_receives_activities(self):
        """Callback server receives and records activities."""
        callback_server = AiohttpCallbackServer(port=9908)
        
        async with callback_server.listen() as transcript:
            # Post activity to callback server
            async with ClientSession() as session:
                activity = Activity(type=ActivityTypes.message, text="Callback message")
                async with session.post(
                    f"{callback_server.service_endpoint}test-conversation/activities",
                    json=activity.model_dump(by_alias=True, exclude_none=True, mode="json")
                ) as response:
                    assert response.status == 200
            
            # Verify transcript recorded the activity
            history = transcript.history()
            assert len(history) == 1
            assert history[0].responses[0].text == "Callback message"

    @pytest.mark.asyncio
    async def test_callback_server_multiple_activities(self):
        """Callback server handles multiple incoming activities."""
        callback_server = AiohttpCallbackServer(port=9909)
        
        async with callback_server.listen() as transcript:
            async with ClientSession() as session:
                for i in range(3):
                    activity = Activity(type=ActivityTypes.message, text=f"Message {i+1}")
                    await session.post(
                        f"{callback_server.service_endpoint}conv/activities",
                        json=activity.model_dump(by_alias=True, exclude_none=True, mode="json")
                    )
            
            history = transcript.history()
            assert len(history) == 3
            assert history[0].responses[0].text == "Message 1"
            assert history[1].responses[0].text == "Message 2"
            assert history[2].responses[0].text == "Message 3"

    @pytest.mark.asyncio
    async def test_callback_server_shares_transcript(self):
        """Callback server can use provided transcript."""
        callback_server = AiohttpCallbackServer(port=9910)
        parent_transcript = Transcript()
        
        # Record something before callback server
        parent_transcript.record(Exchange(
            request=Activity(type=ActivityTypes.message, text="Initial")
        ))
        
        async with callback_server.listen(transcript=parent_transcript) as transcript:
            async with ClientSession() as session:
                activity = Activity(type=ActivityTypes.message, text="Callback")
                await session.post(
                    f"{callback_server.service_endpoint}conv/activities",
                    json=activity.model_dump(by_alias=True, exclude_none=True, mode="json")
                )
        
        # Should have initial + callback
        assert len(parent_transcript.history()) == 2


# ============================================================================
# AiohttpClientFactory Integration Tests
# ============================================================================

class TestAiohttpClientFactoryIntegration:
    """Integration tests for AiohttpClientFactory."""

    @pytest.mark.asyncio
    async def test_factory_creates_working_client(self):
        """Factory creates clients that can communicate with agent."""
        mock_server = MockAgentServer(port=9911)
        mock_server.default_response(Activity(type=ActivityTypes.message, text="Factory test OK"))
        
        async with mock_server.run():
            transcript = Transcript()
            factory = AiohttpClientFactory(
                agent_url=mock_server.endpoint,
                response_endpoint="http://localhost:9999/callback",
                sdk_config={},
                default_template=ActivityTemplate(channel_id="test"),
                default_config=ClientConfig(),
                transcript=transcript,
            )
            
            try:
                client = await factory.create_client()
                responses = await client.send_expect_replies("Test message")
                
                assert len(responses) == 1
                assert responses[0].text == "Factory test OK"
            finally:
                await factory.cleanup()

    @pytest.mark.asyncio
    async def test_factory_applies_default_template(self):
        """Factory applies default template to created clients."""
        mock_server = MockAgentServer(port=9912)
        mock_server.default_response(Activity(type=ActivityTypes.message, text="OK"))
        
        default_template = ActivityTemplate(
            channel_id="factory-channel",
            locale="en-US",
            **{"recipient.id": "agent-123"}
        )
        
        async with mock_server.run():
            transcript = Transcript()
            factory = AiohttpClientFactory(
                agent_url=mock_server.endpoint,
                response_endpoint="http://localhost:9999/callback",
                sdk_config={},
                default_template=default_template,
                default_config=ClientConfig(),
                transcript=transcript,
            )
            
            try:
                client = await factory.create_client()
                await client.send_expect_replies("Test")
                
                received = mock_server.received_activities[0]
                assert received.channel_id == "factory-channel"
                assert received.locale == "en-US"
            finally:
                await factory.cleanup()

    @pytest.mark.asyncio
    async def test_factory_creates_multiple_clients(self):
        """Factory can create multiple independent clients."""
        mock_server = MockAgentServer(port=9913)
        mock_server.default_response(Activity(type=ActivityTypes.message, text="OK"))
        
        async with mock_server.run():
            transcript = Transcript()
            factory = AiohttpClientFactory(
                agent_url=mock_server.endpoint,
                response_endpoint="http://localhost:9999/callback",
                sdk_config={},
                default_template=ActivityTemplate(),
                default_config=ClientConfig(),
                transcript=transcript,
            )
            
            try:
                client1 = await factory.create_client(
                    ClientConfig().with_user("user-1", "Alice")
                )
                client2 = await factory.create_client(
                    ClientConfig().with_user("user-2", "Bob")
                )
                
                await client1.send_expect_replies("From Alice")
                await client2.send_expect_replies("From Bob")
                
                assert len(mock_server.received_activities) == 2
                # Both share the same transcript
                assert len(transcript.history()) == 2
            finally:
                await factory.cleanup()

    @pytest.mark.asyncio
    async def test_factory_cleanup_closes_sessions(self):
        """Factory cleanup closes all created sessions."""
        mock_server = MockAgentServer(port=9914)
        
        async with mock_server.run():
            factory = AiohttpClientFactory(
                agent_url=mock_server.endpoint,
                response_endpoint="http://localhost:9999/callback",
                sdk_config={},
                default_template=ActivityTemplate(),
                default_config=ClientConfig(),
                transcript=Transcript(),
            )
            
            await factory.create_client()
            await factory.create_client()
            
            assert len(factory._sessions) == 2
            
            await factory.cleanup()
            
            assert len(factory._sessions) == 0


# ============================================================================
# ExternalScenario Integration Tests
# ============================================================================

class TestExternalScenarioIntegration:
    """Integration tests for ExternalScenario."""

    def test_external_scenario_requires_endpoint(self):
        """ExternalScenario requires endpoint."""
        with pytest.raises(ValueError, match="endpoint must be provided"):
            ExternalScenario(endpoint="")

    def test_external_scenario_stores_endpoint(self):
        """ExternalScenario stores the provided endpoint."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        assert scenario._endpoint == "http://localhost:3978"

    def test_external_scenario_uses_default_config(self):
        """ExternalScenario uses default config when not provided."""
        scenario = ExternalScenario(endpoint="http://localhost:3978")
        assert isinstance(scenario._config, ScenarioConfig)

    def test_external_scenario_accepts_custom_config(self):
        """ExternalScenario accepts custom config."""
        custom_config = ScenarioConfig(
            env_file_path=".env.test",
            callback_server_port=8080,
        )
        scenario = ExternalScenario(
            endpoint="http://localhost:3978",
            config=custom_config
        )
        assert scenario._config.env_file_path == ".env.test"
        assert scenario._config.callback_server_port == 8080


# ============================================================================
# Full End-to-End Integration Tests
# ============================================================================

class TestEndToEndIntegration:
    """Full end-to-end integration tests demonstrating complete workflows."""

    @pytest.mark.asyncio
    async def test_complete_http_conversation_flow(self):
        """Complete conversation flow using real HTTP infrastructure."""
        mock_server = MockAgentServer(port=9920)
        mock_server.on_text("start", 
            Activity(type=ActivityTypes.message, text="Welcome! I'm a test agent.")
        )
        mock_server.on_text("help",
            Activity(type=ActivityTypes.message, text="I can help with:"),
            Activity(type=ActivityTypes.message, text="- Questions"),
            Activity(type=ActivityTypes.message, text="- Tasks"),
        )
        mock_server.default_response(
            Activity(type=ActivityTypes.message, text="I didn't understand that.")
        )
        
        async with mock_server.run():
            # Setup infrastructure
            transcript = Transcript()
            factory = AiohttpClientFactory(
                agent_url=mock_server.endpoint,
                response_endpoint="http://localhost:9999/callback",
                sdk_config={},
                default_template=ActivityTemplate(
                    channel_id="e2e-test",
                    locale="en-US",
                    **{
                        "conversation.id": "e2e-conv",
                        "from.id": "e2e-user",
                        "from.name": "E2E Test User",
                    }
                ),
                default_config=ClientConfig(),
                transcript=transcript,
            )
            
            try:
                client = await factory.create_client()
                
                # Start conversation
                responses = await client.send_expect_replies("start")
                assert len(responses) == 1
                assert "Welcome" in responses[0].text
                
                # Ask for help
                responses = await client.send_expect_replies("help")
                assert len(responses) == 3
                
                # Verify using Select
                help_messages = Select(responses).get()
                assert len(help_messages) == 3
                
                # Verify using Expect
                Expect(responses).that(type=ActivityTypes.message)
                
                # Unknown input
                responses = await client.send_expect_replies("asdfasdf")
                assert "didn't understand" in responses[0].text
                
                # Verify full history
                history = client.ex_history()
                assert len(history) == 3
                
            finally:
                await factory.cleanup()

    @pytest.mark.asyncio
    async def test_multi_user_http_conversation(self):
        """Multiple users in same conversation via HTTP."""
        mock_server = MockAgentServer(port=9921)
        mock_server.default_response(Activity(type=ActivityTypes.message, text="Received"))
        
        async with mock_server.run():
            transcript = Transcript()
            factory = AiohttpClientFactory(
                agent_url=mock_server.endpoint,
                response_endpoint="http://localhost:9999/callback",
                sdk_config={},
                default_template=ActivityTemplate(**{"conversation.id": "multi-user-conv"}),
                default_config=ClientConfig(),
                transcript=transcript,
            )
            
            try:
                # Create clients for different users
                alice = await factory.create_client(
                    ClientConfig().with_user("alice", "Alice")
                )
                bob = await factory.create_client(
                    ClientConfig().with_user("bob", "Bob")
                )
                
                # Both users send messages
                await alice.send_expect_replies("Hello from Alice")
                await bob.send_expect_replies("Hello from Bob")
                await alice.send_expect_replies("Alice again")
                
                # Verify all messages in shared transcript
                assert len(transcript.history()) == 3
                
                # Verify server received from both users
                from_ids = [a.from_property.id for a in mock_server.received_activities]
                assert "alice" in from_ids
                assert "bob" in from_ids
                
            finally:
                await factory.cleanup()

    @pytest.mark.asyncio
    async def test_invoke_and_message_mixed_flow(self):
        """Mixed invoke and message activities in single conversation."""
        mock_server = MockAgentServer(port=9922)
        mock_server.on_invoke("get/status", 200, {"status": "healthy", "uptime": 12345})
        mock_server.on_invoke("submit/data", 200, {"success": True, "id": "data-789"})
        mock_server.default_response(Activity(type=ActivityTypes.message, text="Message received"))
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                client = AgentClient(sender=sender)
                
                # Regular message
                msg_response = await client.send_expect_replies("Hello")
                assert msg_response[0].text == "Message received"
                
                # Invoke to get status
                status = await client.invoke(
                    Activity(type=ActivityTypes.invoke, name="get/status")
                )
                assert status.body["status"] == "healthy"
                
                # Another message
                await client.send_expect_replies("Still here")
                
                # Invoke to submit data
                submit = await client.invoke(
                    Activity(type=ActivityTypes.invoke, name="submit/data", value={"data": "test"})
                )
                assert submit.body["success"] is True
                
                # Verify full exchange history
                history = client.ex_history()
                assert len(history) == 4
                
                # Filter to just invokes
                invoke_exchanges = [
                    ex for ex in history 
                    if ex.request.type == ActivityTypes.invoke
                ]
                assert len(invoke_exchanges) == 2

    @pytest.mark.asyncio
    async def test_select_and_expect_with_http_responses(self):
        """Select and Expect work correctly with HTTP responses."""
        mock_server = MockAgentServer(port=9924)
        mock_server.on_text("report",
            Activity(type=ActivityTypes.typing),
            Activity(type=ActivityTypes.message, text="Generating report..."),
            Activity(type=ActivityTypes.message, text="Report: Sales up 20%"),
            Activity(type=ActivityTypes.event, name="report.complete"),
        )
        
        async with mock_server.run():
            async with ClientSession(base_url=mock_server.endpoint) as session:
                sender = AiohttpSender(session)
                client = AgentClient(sender=sender)
                
                responses = await client.send_expect_replies("report")
                
                # Use Select to filter
                messages = Select(responses).where(
                    lambda x: x.type == ActivityTypes.message
                ).get()
                assert len(messages) == 2
                
                typing = Select(responses).where(
                    lambda x: x.type == ActivityTypes.typing
                ).get()
                assert len(typing) == 1
                
                events = Select(responses).where(
                    lambda x: x.type == ActivityTypes.event
                ).get()
                assert len(events) == 1
                assert events[0].name == "report.complete"
                
                # Use Expect to validate
                Expect(messages).that(lambda x: x.text is not None)
                
                # Get last message
                last_msg = Select(messages).last().get()[0]
                assert "Sales up 20%" in last_msg.text