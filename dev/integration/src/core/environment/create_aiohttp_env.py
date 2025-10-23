from typing import Optional

from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

from .environment import Environment

def create_aiohttp_env(environ_dict: Optional[dict] = None) -> Environment:

    environ_dict = environ_dict or {}

    agents_sdk_config = load_configuration_from_env(environ_dict)

    storage = MemoryStorage()
    connection_manager = MsalConnectionManager(**agents_sdk_config)
    adapter = CloudAdapter(connection_manager=connection_manager)
    authorization = Authorization(storage, connection_manager, **agents_sdk_config)

    agent_application = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
        authorization=authorization,
        **agents_sdk_config
    )

    return Environment(
        agent_application=agent_application,
        storage=storage,
        connections=connection_manager,
        adapter=adapter,
        authorization=authorization,
        config=agents_sdk_config
    )