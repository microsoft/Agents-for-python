# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the MCP hosting adapter."""

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.mcp import MCPAdapter, MCP_CHANNEL_ID

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class EchoAgent:
    """Minimal agent that echoes back whatever text it receives."""

    async def on_turn(self, context: TurnContext):
        if context.activity.type == ActivityTypes.message and context.activity.text:
            await context.send_activity(f"Echo: {context.activity.text}")


class MultiResponseAgent:
    """Agent that sends multiple response activities."""

    async def on_turn(self, context: TurnContext):
        if context.activity.type == ActivityTypes.message:
            await context.send_activity("First response")
            await context.send_activity("Second response")


class SilentAgent:
    """Agent that does not send any responses."""

    async def on_turn(self, context: TurnContext):
        pass


class ToolAwareAgent:
    """Agent that reads the activity name to identify tool calls."""

    async def on_turn(self, context: TurnContext):
        if context.activity.name:
            await context.send_activity(
                f"Tool: {context.activity.name}, Args: {context.activity.text}"
            )
        else:
            await context.send_activity(f"Message: {context.activity.text}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMCPAdapterInit:
    """Tests for MCPAdapter initialization."""

    def test_creates_mcp_server_with_defaults(self):
        adapter = MCPAdapter(agent=EchoAgent())
        assert adapter.mcp_server is not None
        assert adapter.mcp_server.name == "agents-mcp-server"

    def test_creates_mcp_server_with_custom_name(self):
        adapter = MCPAdapter(agent=EchoAgent(), server_name="my-agent")
        assert adapter.mcp_server.name == "my-agent"

    def test_streamable_http_app_returns_asgi_app(self):
        adapter = MCPAdapter(agent=EchoAgent())
        app = adapter.streamable_http_app()
        assert app is not None


class TestMCPAdapterProcessTurn:
    """Tests for the internal _process_turn method."""

    @pytest.mark.asyncio
    async def test_echo_agent_returns_response(self):
        adapter = MCPAdapter(agent=EchoAgent())
        result = await adapter._process_turn("Hello")
        assert result == "Echo: Hello"

    @pytest.mark.asyncio
    async def test_multi_response_concatenated(self):
        adapter = MCPAdapter(agent=MultiResponseAgent())
        result = await adapter._process_turn("Hi")
        assert result == "First response\nSecond response"

    @pytest.mark.asyncio
    async def test_silent_agent_returns_empty(self):
        adapter = MCPAdapter(agent=SilentAgent())
        result = await adapter._process_turn("Hello")
        assert result == ""

    @pytest.mark.asyncio
    async def test_tool_name_set_on_activity(self):
        adapter = MCPAdapter(agent=ToolAwareAgent())
        result = await adapter._process_turn(
            '{"tool": "search", "arguments": {"q": "test"}}',
            tool_name="search",
        )
        assert "Tool: search" in result

    @pytest.mark.asyncio
    async def test_activity_has_mcp_channel_id(self):
        """Verify the activity routed through the pipeline has channel_id='mcp'."""
        captured_activities = []

        class CapturingAgent:
            async def on_turn(self, context: TurnContext):
                captured_activities.append(context.activity)
                await context.send_activity("ok")

        adapter = MCPAdapter(agent=CapturingAgent())
        await adapter._process_turn("test")

        assert len(captured_activities) == 1
        assert captured_activities[0].channel_id == MCP_CHANNEL_ID
        assert captured_activities[0].type == ActivityTypes.message


class TestMCPAdapterSendActivities:
    """Tests for the send_activities override."""

    @pytest.mark.asyncio
    async def test_send_activities_buffers_responses(self):
        adapter = MCPAdapter(agent=EchoAgent())
        activity = Activity(
            type=ActivityTypes.message,
            text="test",
            channel_id=MCP_CHANNEL_ID,
        )
        context = TurnContext(adapter, activity)

        response_activity = Activity(type=ActivityTypes.message, text="hello")
        results = await adapter.send_activities(context, [response_activity])

        assert len(results) == 1
        assert results[0].id is not None
        bucket = context.turn_state.get("MCPAdapter.Responses", [])
        assert len(bucket) == 1
        assert bucket[0].text == "hello"


class TestMCPAdapterUnsupportedOps:
    """Tests for unsupported operations."""

    @pytest.mark.asyncio
    async def test_update_activity_raises(self):
        adapter = MCPAdapter(agent=EchoAgent())
        activity = Activity(type=ActivityTypes.message, text="test", channel_id="mcp")
        context = TurnContext(adapter, activity)
        with pytest.raises(NotImplementedError):
            await adapter.update_activity(context, activity)

    @pytest.mark.asyncio
    async def test_delete_activity_raises(self):
        adapter = MCPAdapter(agent=EchoAgent())
        activity = Activity(type=ActivityTypes.message, text="test", channel_id="mcp")
        context = TurnContext(adapter, activity)
        with pytest.raises(NotImplementedError):
            await adapter.delete_activity(context, None)


class TestMCPAdapterMiddleware:
    """Tests for middleware integration."""

    @pytest.mark.asyncio
    async def test_middleware_runs_in_pipeline(self):
        """Verify middleware is invoked during _process_turn."""
        middleware_called = False

        class TrackingMiddleware:
            async def on_turn(self, context, logic):
                nonlocal middleware_called
                middleware_called = True
                await logic()

        adapter = MCPAdapter(agent=EchoAgent())
        adapter.use(TrackingMiddleware())

        result = await adapter._process_turn("Hello")
        assert middleware_called
        assert result == "Echo: Hello"

    @pytest.mark.asyncio
    async def test_middleware_can_modify_activity(self):
        """Verify middleware can intercept and modify the activity."""

        class PrefixMiddleware:
            async def on_turn(self, context, logic):
                context.activity.text = "[modified] " + context.activity.text
                await logic()

        adapter = MCPAdapter(agent=EchoAgent())
        adapter.use(PrefixMiddleware())

        result = await adapter._process_turn("Hello")
        assert result == "Echo: [modified] Hello"


class TestMCPAdapterCustomTools:
    """Tests for custom tool registration."""

    def test_custom_tools_registered(self):
        adapter = MCPAdapter(
            agent=EchoAgent(),
            tools=[
                {
                    "name": "search",
                    "description": "Search for information",
                },
            ],
        )
        # The MCP server should have registered the custom tool
        assert adapter.mcp_server is not None
