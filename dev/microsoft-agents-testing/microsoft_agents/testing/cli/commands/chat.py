# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Chat command - Interactive conversation with an agent.

Provides a REPL-style interface for sending messages to an agent
and viewing responses in real-time.
"""

import click

from microsoft_agents.testing.core import (
    ScenarioConfig,
    ExternalScenario,
)
from microsoft_agents.testing.transcript_logger import _print_messages

from ..config import CLIConfig
from ..core import Output, async_command

@click.command()
@click.option(
    "--url", "-u",
    default=None,
    help="Override the agent URL to check.",
)
@click.pass_context
@async_command
async def chat(ctx: click.Context, url: str | None) -> None:
    """Check if the agent endpoint is reachable.
    
    Sends a simple request to verify the agent is online and responding.
    """
    config: CLIConfig = ctx.obj["config"]
    verbose: bool = ctx.obj.get("verbose", False)
    out = Output(verbose=verbose)

    scenario = ExternalScenario(
        url or config.agent_url,
        ScenarioConfig(
            env_file_path = config.env_path,
        )
    )

    async with scenario.client() as client:

        # client.template = client.template.with_defaults({
        #     "delivery_mode": "expect_replies",
        # })

        while True:

            out.info("Enter a message to send to the agent (or 'exit' to quit):")
            user_input = out.prompt()
            if user_input.lower() == "exit":
                break
            out.newline()

            replies = await client.send_expect_replies(user_input)
            for reply in replies:
                out.info(f"agent: {reply.text}")
                out.newline()
            
        out.success("Exiting console.")

        transcript = client.transcript
        _print_messages(transcript)