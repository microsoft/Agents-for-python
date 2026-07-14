# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import click

from microsoft_agents.testing.cli.core import (
    async_command,
    pass_output,
    Output,
    with_scenario,
)
from microsoft_agents.testing.core import (
    Scenario,
    ExternalScenario
)

from .scenario_group import scenario_group

@scenario_group.command("run")
@async_command
@pass_output
@with_scenario
async def run(out: Output, scenario: Scenario) -> None:
    """Run a specified test scenario as a long-running server.

    Only in-process scenarios (AiohttpScenario) are supported.
    External scenarios cannot be "run" since they are already running.

    :param out: CLI output helper.
    :param scenario: The resolved Scenario instance.
    """
    if isinstance(scenario, ExternalScenario):
        out.error("Running an ExternalScenario is not supported in this command. Please use specific commands designed for interaction, such as 'chat' or 'post'.")
        raise click.Abort()
    
    try:
        async with scenario.run():
            out.newline()
            out.info("🚀 Scenario is running at http://localhost:3978...")
            out.info("Press Ctrl+C to stop.")
            out.newline()
            # Block forever until KeyboardInterrupt
            await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    
    out.newline()
    out.success("Scenario stopped.")