from typing import Awaitable, Callable
from dataclasses import dataclass

from microsoft_agents.hosting.core import (
    AgentApplication,
    ChannelAdapter,
    Connections,
    Authorization,
    Storage,
    TurnState,
)

@dataclass
class Environment:
    """A sample data object for integration tests."""

    agent_application: AgentApplication[TurnState]
    storage: Storage
    adapter: ChannelAdapter
    connections: Connections
    authorization: Authorization

    config: dict

    driver: Callable[[], Awaitable[None]]