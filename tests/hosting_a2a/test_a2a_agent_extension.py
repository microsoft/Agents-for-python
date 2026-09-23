# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.hosting.core import AgentApplication
from microsoft_agents.hosting.a2a.a2a_agent_extension import A2AAgentExtension


def test_message_registers_wrapped_handler_with_core_application():
    app = MagicMock(spec=AgentApplication)
    core_decorator = MagicMock(return_value="registered-handler")
    app.message.return_value = core_decorator
    extension = A2AAgentExtension(app)
    handler = AsyncMock()
    wrapped_handler = AsyncMock()

    with patch(
        "microsoft_agents.hosting.a2a.a2a_agent_extension.wrap_a2a_route_handler",
        return_value=wrapped_handler,
    ) as wrap_handler:
        result = extension.message(
            ["hello", "help"],
            auth_handlers=["auth"],
            rank=10,
        )(handler)

    app.message.assert_called_once_with(
        ["hello", "help"],
        auth_handlers=["auth"],
        rank=10,
    )
    wrap_handler.assert_called_once_with(handler, app)
    core_decorator.assert_called_once_with(wrapped_handler)
    assert result == "registered-handler"
