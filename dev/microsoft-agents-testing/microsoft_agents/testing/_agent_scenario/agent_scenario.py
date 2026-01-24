# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import dotenv_values

from microsoft_agents.activity import (
    load_configuration_from_env,
    Activity
)

from microsoft_agents.testing.utils import ModelTemplate, ActivityTemplate

from .agent_client import AgentClient

DEFAULT_ACTIVITY_TEMPLATE = ActivityTemplate({
    "type": "message",
    "channel_id": "test",
    "conversation.id": "conv-id",
    "locale": "en-US",
    "from.id": "user-id",
    "from.name": "User",
    "recipient.id": "agent-id",
    "recipient.name": "Agent",
    "text": "",
})

class AgentScenarioConfig:
    """Configuration for an agent test scenario."""

    env_file_path: str = ".env"
    response_server_port: int = 9378

    activity_template: ModelTemplate[Activity] = DEFAULT_ACTIVITY_TEMPLATE


class AgentScenario(ABC):
    """Base class for an agent test scenario."""

    def __init__(self, config: AgentScenarioConfig | None = None) -> None:
        """Initialize the agent scenario with the given configuration.
        
        :param config: The configuration for the agent scenario.
        """
        
        self._config = config or AgentScenarioConfig()

        env_vars = dotenv_values(self._config.env_file_path)
        self._sdk_config = load_configuration_from_env(env_vars)

    @abstractmethod
    @asynccontextmanager
    async def client(self) -> AsyncIterator[AgentClient]:
        """Get an asynchronous context manager for the agent client.
        
        :yield: An asynchronous iterator that yields an AgentClient.
        """
        raise NotImplementedError()