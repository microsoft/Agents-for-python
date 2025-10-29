from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from microsoft_agents.hosting.core import (
    AgentApplication,
    ChannelAdapter,
    Connections,
    Authorization,
    Storage,
    TurnState,
)

from .application_runner import ApplicationRunner

class Environment(ABC):
    """A sample data object for integration tests."""

    agent_application: AgentApplication[TurnState]
    storage: Storage
    adapter: ChannelAdapter
    connections: Connections
    authorization: Authorization

    config: dict

    driver: Callable[[], Awaitable[None]]

    @abstractmethod
    async def init_env(self) -> None:
        """Initialize the environment."""
        raise NotImplementedError()

    @abstractmethod
    def create_runner(self) -> ApplicationRunner:
        """Create an application runner for the environment."""
        raise NotImplementedError()
    
    @abstractmethod
    def create_app(self):
        """Create the application for the environment."""
        raise NotImplementedError()