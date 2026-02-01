# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Microsoft Agents Testing Framework.

This package provides a comprehensive testing framework for M365 Agents SDK for Python.
It enables testing agents through both in-process scenarios and external HTTP endpoints.

Key Components:
    - **AgentClient**: Main client for sending activities and collecting responses.
    - **Scenario / AiohttpScenario / ExternalScenario**: Test scenario orchestrators.
    - **Expect / Select**: Fluent assertion and selection utilities for test validation.
    - **Transcript / Exchange**: Request-response recording for debugging and analysis.
    - **send / ex_send**: Simple utility functions for quick agent interactions.

Example:
    Basic usage with an external agent::

        from microsoft_agents.testing import ExternalScenario

        scenario = ExternalScenario("http://localhost:3978/api/messages")
        async with scenario.client() as client:
            replies = await client.send("Hello!")
            client.expect().that_for_any(text="~Hello")

    Using the fluent assertion API::

        from microsoft_agents.testing import Expect, Select

        # Assert all responses are messages
        Expect(responses).that(type="message")

        # Filter and assert
        Select(responses).where(type="message").expect().that(text="~world")
"""

from .core import (
    AgentClient,
    ScenarioConfig,
    ClientConfig,
    ActivityTemplate,
    Scenario,
    ExternalScenario,
    AiohttpCallbackServer,
    AiohttpSender,
    CallbackServer,
    Sender,
    Transcript,
    Exchange,
    Expect,
    Select,
    Unset,
)

from .aiohttp_scenario import (
    AgentEnvironment,
    AiohttpScenario,
)

from .transcript_logger import (
    DetailLevel,
    ConversationLogger,
    ActivityLogger,
    TranscriptFormatter,
)

from .utils import (
    send,
    ex_send,
)

__all__ = [
    "AgentClient",
    "ScenarioConfig",
    "ClientConfig",
    "ActivityTemplate",
    "Scenario",
    "ExternalScenario",
    "AiohttpCallbackServer",
    "AiohttpSender",
    "CallbackServer",
    "Sender",
    "Transcript",
    "Exchange",
    "Expect",
    "Select",
    "Unset",
    "AgentEnvironment",
    "AiohttpScenario",
    "send",
    "ex_send",
    "DetailLevel",
    "ConversationLogger",
    "ActivityLogger",
    "TranscriptFormatter",
]