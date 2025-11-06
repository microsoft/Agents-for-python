from typing import Optional
from fastapi import Request, Response
from microsoft_agents.hosting.core import error_resources
from microsoft_agents.hosting.core.app import AgentApplication
from .cloud_adapter import CloudAdapter


async def start_agent_process(
    request: Request,
    agent_application: AgentApplication,
    adapter: CloudAdapter,
) -> Optional[Response]:
    """Starts the agent host with the provided adapter and agent application.
    Args:
        adapter (CloudAdapter): The adapter to use for the agent host.
        agent_application (AgentApplication): The agent application to run.
    """
    if not adapter:
        raise TypeError(str(error_resources.AdapterRequired))
    if not agent_application:
        raise TypeError(str(error_resources.AgentApplicationRequired))

    # Start the agent application with the provided adapter
    return await adapter.process(
        request,
        agent_application,
    )
