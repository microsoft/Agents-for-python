# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import click

from ..config import CLIConfig
from ..core import Output, async_command

from ..scenarios import SCENARIOS

@click.command()
@click.option(
    "--scenario", "-s",
    default=None,
    help="Specify the scenario to run.",
)
@click.pass_context
@async_command
async def run(ctx: click.Context, scenario: str | None) -> None:
    """Check if the agent endpoint is reachable.
    
    Sends a simple request to verify the agent is online and responding.
    """
    config: CLIConfig = ctx.obj["config"]
    verbose: bool = ctx.obj.get("verbose", False)
    out = Output(verbose=verbose)

    if not scenario or scenario not in SCENARIOS:
        out.error("Invalid or missing scenario. Available scenarios:")
        raise click.Abort()
    
    ins = SCENARIOS[scenario]

    async with ins.client():
        while True:
            pass