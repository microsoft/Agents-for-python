# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Health command - checks agent connectivity."""

import click

from ..config import CLIConfig
from ..core import Output, async_command

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
@click.pass_context
@async_command
async def console(ctx: click.Context, url: str | None) -> None:
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
        while True:

            out.info("Enter a message to send to the agent (or 'exit' to quit):")
            user_input = out.prompt()
            if user_input.lower() == "exit":
                break
            out.newline()

            replies = await client.send_expect_replies(user_input)
            for reply in replies:
                out.echo(f"agent: {reply.text}")
                out.newline()
            
        out.success("Exiting console.")