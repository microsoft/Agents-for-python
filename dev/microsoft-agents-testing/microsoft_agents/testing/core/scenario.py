# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Base scenario abstractions for agent testing.

This module defines the core Scenario class and ClientFactory protocol
that form the foundation of the testing framework's scenario-based approach.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Protocol, AsyncContextManager

from .agent_client import AgentClient
from .config import ClientConfig, ScenarioConfig


class ClientFactory(Protocol):
    """Protocol for creating AgentClient instances within a running scenario.
    
    Implementations of this protocol are yielded by Scenario.run() and allow
    creating multiple clients with different configurations during a single
    test scenario.
    """
    
    async def __call__(self, config: ClientConfig | None = None) -> AgentClient:
        """Create a new client with the given configuration.
        
        :param config: Optional client configuration. If None, uses defaults.
        :return: A configured AgentClient instance.
        """
        ...


class Scenario(ABC):
    """Base class for agent test scenarios.
    
    A Scenario manages the lifecycle of testing infrastructure (servers,
    connections, etc.) and provides a factory for creating test clients.
    
    Subclasses implement specific hosting strategies:
    - ExternalScenario: Tests against an externally-hosted agent
    - AiohttpScenario: Hosts the agent in-process for integration testing
    """
    
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