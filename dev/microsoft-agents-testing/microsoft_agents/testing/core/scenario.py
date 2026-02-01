# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Protocol, AsyncContextManager

from .agent_client import AgentClient
from .config import ClientConfig, ScenarioConfig
from .fluent import ActivityTemplate


def _default_activity_template() -> ActivityTemplate:
    """Create a default activity template with all required fields."""
    return ActivityTemplate({
        "type": "message",
        "channel_id": "test",
        "conversation.id": "test-conversation",
        "locale": "en-US",
        "from.id": "user-id",
        "from.name": "User",
        "recipient.id": "agent-id",
        "recipient.name": "Agent",
    })

class ClientFactory(Protocol):
    """Protocol for creating clients within a running scenario."""
    
    async def __call__(self, config: ClientConfig | None = None) -> AgentClient:
        """Create a new client with the given configuration."""
        ...

class Scenario(ABC):
    """Base class for agent test scenarios."""
    
    def __init__(self, config: ScenarioConfig | None = None) -> None:
        self._config = config or ScenarioConfig()

    @abstractmethod
    def run(self) -> AsyncContextManager[ClientFactory]:
        """Start the scenario infrastructure and yield a client factory.
        
        Usage:
            async with scenario.run() as factory:
                client = await factory()
                # or with custom config
                client2 = await factory(
                    ClientConfig().with_user("user-2", "Second User")
                )
        """
    
    # Convenience method for simple single-client usage
    @asynccontextmanager
    async def client(self, config: ClientConfig | None = None) -> AsyncIterator[AgentClient]:
        """Convenience: start scenario and yield a single client."""
        async with self.run() as factory:
            client = await factory(config)
            yield client