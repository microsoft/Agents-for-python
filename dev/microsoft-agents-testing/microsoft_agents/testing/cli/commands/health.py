# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Health command - checks agent connectivity."""

import click

from ..config import CLIConfig
from ..core import Output, async_command

from microsoft_agents.activity import Activity

from microsoft_agents.testing.agent_scenario import (
    AgentScenarioConfig,
    ExternalAgentScenario,
)

@click.command()
@click.option(
    "--url", "-u",
    default=None,
    help="Override the agent URL to check.",
)
@click.option(
    "--timeout", "-t",
    default=10,
    help="Request timeout in seconds.",
    type=int,
)
@click.pass_context
@async_command
async def health(ctx: click.Context, url: str | None, timeout: int) -> None:
    """Check if the agent endpoint is reachable.
    
    Sends a simple request to verify the agent is online and responding.
    """
    config: CLIConfig = ctx.obj["config"]
    verbose: bool = ctx.obj.get("verbose", False)
    out = Output(verbose=verbose)

    scenario = ExternalAgentScenario(
        url or config.agent_url,
        AgentScenarioConfig(
            env_file_path = config.env_path,
        )
    )
    async with scenario.client() as client:

        activity = Activity(
            type="message",
            text="Health check",
        )
        
        await client.send(activity)
        out.success(f"Agent is reachable at {client.base_url}")