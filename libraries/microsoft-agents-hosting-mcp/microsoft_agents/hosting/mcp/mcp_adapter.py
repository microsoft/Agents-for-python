# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""MCP hosting adapter for the Microsoft 365 Agents SDK.

This module provides an adapter that exposes an M365 Agent as an MCP server,
translating MCP tool calls into Activity-based turns processed by the agent
pipeline.
"""

from __future__ import annotations

import uuid
from typing import Any, List

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
    ResourceResponse,
)
from microsoft_agents.hosting.core.channel_adapter import ChannelAdapter
from microsoft_agents.hosting.core.turn_context import TurnContext
from microsoft_agents.hosting.core.agent import Agent

from mcp.server.fastmcp import FastMCP

# Channel identifier for MCP-originated activities.
MCP_CHANNEL_ID = "mcp"


class MCPAdapter(ChannelAdapter):
    """Adapter that bridges MCP protocol requests to the Agents SDK pipeline.

    The adapter registers a ``message`` tool on the MCP server.  When an MCP
    client invokes that tool, the adapter constructs an
    :class:`~microsoft_agents.activity.Activity`, creates a
    :class:`~microsoft_agents.hosting.core.turn_context.TurnContext`, and routes
    the turn through the standard middleware → agent handler pipeline.

    Responses sent by the agent via ``context.send_activity()`` are collected
    and returned as MCP tool-call results.

    Args:
        agent: The agent instance that handles incoming turns.
        server_name: Display name for the MCP server (defaults to
            ``"agents-mcp-server"``).
        server_instructions: Optional instructions exposed to MCP clients
            describing the server's capabilities.
        tools: Optional list of additional MCP tool descriptors.  Each entry
            is a dict with ``name``, ``description``, and an optional
            ``parameters`` JSON-schema dict.
    """

    def __init__(
        self,
        agent: Agent,
        *,
        server_name: str = "agents-mcp-server",
        server_instructions: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__()
        self._agent = agent
        self._mcp = FastMCP(
            name=server_name,
            instructions=server_instructions,
        )
        # Register the built-in "message" tool.
        self._register_message_tool()

        # Register any additional custom tools.
        if tools:
            for tool_spec in tools:
                self._register_custom_tool(tool_spec)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def mcp_server(self) -> FastMCP:
        """Return the underlying ``FastMCP`` instance.

        Callers can use this to mount the streamable-HTTP or SSE endpoint on
        a web framework::

            app.mount("/mcp", adapter.mcp_server.streamable_http_app())
        """
        return self._mcp

    def streamable_http_app(self):
        """Convenience shortcut for ``self.mcp_server.streamable_http_app()``."""
        return self._mcp.streamable_http_app()

    # ------------------------------------------------------------------
    # ChannelAdapter abstract method implementations
    # ------------------------------------------------------------------

    async def send_activities(
        self, context: TurnContext, activities: List[Activity]
    ) -> List[ResourceResponse]:
        """Buffer outgoing activities so they can be returned to the MCP client.

        Activities are stored on the turn context under the key
        ``MCPAdapter.Responses`` rather than being sent over a channel.
        """
        responses: list[ResourceResponse] = []
        for activity in activities:
            activity_id = activity.id or str(uuid.uuid4())
            activity.id = activity_id

            # Stash the activity so _process_turn can retrieve it.
            bucket: list[Activity] = context.turn_state.setdefault(
                "MCPAdapter.Responses", []
            )
            bucket.append(activity)

            responses.append(ResourceResponse(id=activity_id))
        return responses

    async def update_activity(self, context: TurnContext, activity: Activity):
        """Not supported for the MCP channel."""
        raise NotImplementedError("update_activity is not supported over MCP")

    async def delete_activity(
        self, context: TurnContext, reference: ConversationReference
    ):
        """Not supported for the MCP channel."""
        raise NotImplementedError("delete_activity is not supported over MCP")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_message_tool(self) -> None:
        """Register the built-in ``message`` tool on the MCP server."""

        @self._mcp.tool(
            name="message",
            description=(
                "Send a message to the agent and receive a response. "
                "Use this tool to communicate with the agent."
            ),
        )
        async def message_tool(text: str) -> str:
            """Send *text* to the agent and return its response."""
            return await self._process_turn(text)

    def _register_custom_tool(self, tool_spec: dict[str, Any]) -> None:
        """Register a custom tool that routes through the agent pipeline.

        The tool call arguments are JSON-serialised and sent as the Activity
        text, with the tool name stored in ``Activity.name``.
        """
        import json

        tool_name = tool_spec["name"]
        tool_description = tool_spec.get("description", "")

        @self._mcp.tool(name=tool_name, description=tool_description)
        async def _custom_handler(**kwargs: Any) -> str:
            text = json.dumps({"tool": tool_name, "arguments": kwargs})
            return await self._process_turn(text, tool_name=tool_name)

    async def _process_turn(self, text: str, *, tool_name: str | None = None) -> str:
        """Create an Activity from *text*, run it through the agent, and
        return the collected response text.
        """
        conversation_id = str(uuid.uuid4())

        activity = Activity(
            type=ActivityTypes.message,
            id=str(uuid.uuid4()),
            text=text,
            channel_id=MCP_CHANNEL_ID,
            from_property=ChannelAccount(id="mcp-user", name="MCP Client"),
            recipient=ChannelAccount(id="agent", name="Agent"),
            conversation=ConversationAccount(id=conversation_id),
            service_url="urn:mcp",
        )

        if tool_name:
            activity.name = tool_name

        context = TurnContext(self, activity)

        # Run the agent pipeline (middleware → agent.on_turn).
        await self.run_pipeline(context, self._agent.on_turn)

        # Collect responses buffered by send_activities().
        response_activities: list[Activity] = context.turn_state.get(
            "MCPAdapter.Responses", []
        )

        # Concatenate all message-text responses.
        parts: list[str] = []
        for resp in response_activities:
            if resp.text:
                parts.append(resp.text)

        return "\n".join(parts) if parts else ""
