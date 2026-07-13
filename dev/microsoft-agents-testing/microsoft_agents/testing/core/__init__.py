# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Core components of the Microsoft Agents Testing framework.

This module provides the foundational classes for building and running
agent test scenarios, including:

- Configuration classes (ScenarioConfig, ClientConfig)
- Scenario abstractions (Scenario, ExternalScenario)
- Client interfaces (AgentClient, Sender)
- Fluent assertion utilities (Expect, Select, ActivityTemplate)
- Transport layer (Transcript, Exchange, CallbackServer)
"""

from .fluent import (
    Expect,
    Select,
    ModelTemplate,
    ActivityTemplate,
    ModelTransform,
    Quantifier,
    Unset,
)

from .transport import (
    Exchange,
    Transcript,
    AiohttpCallbackServer,
    AiohttpSender,
    CallbackServer,
    Sender,
)

from .agent_client import AgentClient
from ._aiohttp_client_factory import _AiohttpClientFactory
from .scenario import Scenario, ScenarioConfig, ClientFactory
from .config import ClientConfig
from .external_scenario import ExternalScenario
from .utils import (
    activities_from_ex,
    sdk_config_connection,
    generate_token,
    generate_token_from_config,
)

__all__ = [
    "Expect",
    "Select",
    "ModelTemplate",
    "ActivityTemplate",
    "ModelTransform",
    "Quantifier",
    "Exchange",
    "Transcript",
    "AiohttpCallbackServer",
    "AiohttpSender",
    "CallbackServer",
    "Sender",
    "AgentClient",
    "Scenario",
    "ClientFactory",
    "ExternalScenario",
    "Unset",
    "_AiohttpClientFactory",
    "ScenarioConfig",
    "ClientConfig",
    "activities_from_ex",
    "sdk_config_connection",
    "generate_token",
    "generate_token_from_config",
]