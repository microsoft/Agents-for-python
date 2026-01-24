from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol

from microsoft_agents.testing.utils import ActivityTemplate
from microsoft_agents.testing.client import AgentClient

from .client_config import ClientConfig

@dataclass
class ScenarioConfig:
    """Configuration for agent test scenarios."""
    env_file_path: str = ".env"
    response_server_port: int = 9378
    activity_template: ActivityTemplate = field(default_factory=ActivityTemplate)
    client_config: ClientConfig = field(default_factory=ClientConfig)

class Scenario(ABC):
    """Base class for agent test scenarios."""
    
    def __init__(self, config: ScenarioConfig | None = None) -> None:
        self._config = config or ScenarioConfig()

    @abstractmethod
    @asynccontextmanager
    async def run(self) -> AsyncIterator[ClientFactory]:
        """Start the scenario infrastructure and yield a client factory.
        
        Usage:
            async with scenario.run() as factory:
                client = await factory.create_client()
                # or with custom config
                client2 = await factory.create_client(
                    ClientConfig().with_user("user-2", "Second User")
                )
        """
        ...
    
    # Convenience method for simple single-client usage
    @asynccontextmanager
    async def client(self, config: ClientConfig | None = None) -> AsyncIterator[AgentClient]:
        """Convenience: start scenario and yield a single client."""
        async with self.run() as factory:
            client = await factory.create_client(config)
            yield client

class ClientFactory(Protocol):
    """Protocol for creating clients within a running scenario."""
    
    async def create_client(self, config: ClientConfig | None = None) -> AgentClient:
        """Create a new client with the given configuration."""
        ...