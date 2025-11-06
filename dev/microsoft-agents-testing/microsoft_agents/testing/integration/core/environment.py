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
    connection_manager: Connections
    authorization: Authorization

    config: dict

    driver: Callable[[], Awaitable[None]]

    @abstractmethod
    async def init_env(self, environ_config: dict) -> None:
        """Initialize the environment."""
        raise NotImplementedError()

    @abstractmethod
    def create_runner(self, *args, **kwargs) -> ApplicationRunner:
        """Create an application runner for the environment.

        Subclasses may accept additional arguments as needed.
        """
        raise NotImplementedError()
