from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
    Authorization
)

from src.extension import Extension

AUTHORIZATION = Authorization()
MEMORY = MemoryStorage()
APP = AgentApplication()

EXTENSION = Extension(app=APP)