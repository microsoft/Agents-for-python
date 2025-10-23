from dataclasses import dataclass

from microsoft_agents.hosting.core import (
    AgentApplication,
    ChannelAdapter,
    Connections
)

@dataclass
class Sample:
    """A sample data object for integration tests."""

    agent_application: AgentApplication
    adapter: ChannelAdapter
    connections: Connections

    config: dict