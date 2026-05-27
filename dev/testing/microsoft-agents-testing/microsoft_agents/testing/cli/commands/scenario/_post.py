import click
import json

from microsoft_agents.activity import Activity
from microsoft_agents.testing.cli.core import (
    async_command,
    pass_output,
    Output,
    with_scenario
)
from microsoft_agents.testing.core import Scenario
from microsoft_agents.testing.formatting import ActivityTranscriptFormatter

from .scenario import scenario


@scenario.command("post")
@async_command
@pass_output
@with_scenario
@click.argument("message", required=False)
@click.option("--json_file", "-j", required=False, type=click.File("rb"), help="Message text or JSON activity to send to the agent.")
@click.option("--wait", "-w", default=5.0, help="Seconds to wait for a response before timing out.")
async def scenario_post(out: Output, scenario: Scenario, message: str | None, json_file, wait: float) -> None:
    """Send a single message or activity to an agent and display the transcript.

    Provide either a text message as an argument or a JSON activity file via --json_file.

    :param out: CLI output helper.
    :param scenario: The resolved Scenario instance.
    :param message: Plain text message to send.
    :param json_file: File handle for a JSON activity payload.
    :param wait: Seconds to wait for async responses.
    """
    
    if not message and not json_file:
        out.error("Either a message argument or --json_file must be provided.")
        return
    
    if message and json_file:
        out.error("Cannot provide both a message argument and --json_file. Please choose one.")
        return
    
    async with scenario.client() as client:
        activity_or_str: Activity | str
        if message:
            assert isinstance(message, str)
            activity_or_str = message
        else:
            data = json.load(json_file)
            activity_or_str = client.template.create(data)

        await client.send(activity_or_str, wait=wait)

    transcript = client.transcript

    text = ActivityTranscriptFormatter().format(transcript)

    out.info("Transcript of the conversation:")
    out.info("=" * 40)
    out.newline()
    out.info(text)
