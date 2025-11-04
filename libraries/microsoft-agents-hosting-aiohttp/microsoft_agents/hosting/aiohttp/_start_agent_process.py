from typing import Optional

from aiohttp.web import Request, Response

from microsoft_agents.hosting.core import (
    AgentApplication,
    start_agent_process as core_start_agent_process,
)

from .cloud_adapter import CloudAdapter


async def start_agent_process(
    request: Request,
    agent_application: AgentApplication,
    adapter: CloudAdapter,
) -> Optional[Response]:
    """Starts the agent host with the provided adapter and agent application."""
    return await core_start_agent_process(request, agent_application, adapter)
