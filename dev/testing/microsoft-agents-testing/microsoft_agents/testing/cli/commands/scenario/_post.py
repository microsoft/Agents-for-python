# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import click

from microsoft_agents.testing.cli.core import (
    async_command,
    pass_output,
    Output,
    with_scenario
)
from microsoft_agents.testing.core import Scenario
from microsoft_agents.testing.formatting import ActivityTranscriptFormatter

from .scenario_group import scenario_group
from ._utils import load_activity


@scenario_group.command("post")
@async_command
@pass_output
@with_scenario
@click.option("--message", "-m", required=False, help="Text message to send to the agent.")
@click.option(
    "--json-file",
    "-j",
    "json_file",
    required=False,
    type=click.File("rb"),
    help="JSON activity to send to the agent.",
)
@click.option(
    "--timeout",
    "-t",
    default=5000,
    type=int,
    help="Milliseconds to wait for a response before timing out.",
)
async def post(out: Output, scenario: Scenario, message: str | None, json_file, timeout: int) -> None:
    """Send a single message or activity to an agent and display the transcript.

    Provide either a text message as an argument or a JSON activity file via --json-file.

    :param out: CLI output helper.
    :param scenario: The resolved Scenario instance.
    :param message: Plain text message to send.
    :param json_file: File handle for a JSON activity payload.
    :param timeout: Milliseconds to wait for a response before timing out.
    """
    
    activity = load_activity(message, json_file, out)
    
    async with scenario.client() as client:
        await client.send(activity, wait=timeout/1000)

    transcript = client.transcript

    text = ActivityTranscriptFormatter(
        model_dump_args={
            "exclude_unset": True,
            "exclude_none": True
        }
    ).format(transcript)

    out.info("Transcript of the conversation:")
    out.info("=" * 40)
    out.newline()
    out.info(text)
