# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Post command - sends a payload to an agent."""

import json
from pathlib import Path

import click

from ..config import CLIConfig
from ..core import Output, async_command

from microsoft_agents.activity import Activity

from microsoft_agents.testing.agent_scenario import (
    AgentScenarioConfig,
    ExternalAgentScenario,
)
from microsoft_agents.testing.utils import ActivityTemplate

def get_payload(out: Output, payload_path: str) -> dict:
    """Load JSON payload from a file."""
    # Load from file
    try:
        with open(payload_path, "r", encoding="utf-8") as f:
            activity = json.load(f)
    except json.JSONDecodeError as e:
        out.error(f"Invalid JSON in payload file: {e}")
        raise click.Abort()
    except FileNotFoundError:
        out.error(f"Payload file not found: {payload_path}")
        out.info("Absolute path: " + str(Path(payload_path).resolve()))
        raise click.Abort()
    
    return activity
    
@click.command()
@click.argument(
    "payload",
    type=click.Path(exists=True),
    required=False,
)
@click.option(
    "--url", "-u",
    default=None,
    help="Override the agent URL.",
)
@click.option(
    "--message", "-m",
    default=None,
    help="Send a simple text message instead of a payload file.",
)
@click.option(
    "--listen_duration", "-l",
    default=5,
    help="Response listening duration in seconds.",
    type=int,
)
@click.pass_context
@async_command
async def post(
    ctx: click.Context,
    payload: str | None,
    url: str | None,
    message: str | None,
    listen_duration: int,
) -> None:
    """Send a payload to an agent.
    
    PAYLOAD is the path to a JSON file containing the activity to send.
    Alternatively, use --message to send a simple text message.
    
    Examples:
    
        \b
        # Send a payload file
        mat post payload.json
        
        \b
        # Send a simple message
        mat post --message "Hello, agent!"
    """
    config: CLIConfig = ctx.obj["config"]
    verbose: bool = ctx.obj.get("verbose", False)
    out = Output(verbose=verbose)
    
    # Build the payload
    if message:
        # Simple message payload
        activity_json = {
            "type": "message",
            "text": message,
        }
    elif payload:
        activity_json = get_payload(out, payload)
    else:
        out.error("No payload specified.")
        out.info("Provide a payload file or use --message option.")
        raise click.Abort()
    
    scenario = ExternalAgentScenario(
        url or config.agent_url,
        AgentScenarioConfig(
            env_file_path = config.env_path,
            activity_template = ActivityTemplate(),
        )
    )

    async with scenario.client() as client:

        activity = Activity.model_validate(activity_json)

        if verbose:
            out.debug("Payload:")
            out.activity(activity)

        responses = await client.send(activity, wait_for=listen_duration)

        out.info("Activity sent successfully.")
        out.info("Received {} response(s).".format(len(responses)))
        out.newline()

        for response in responses:
            out.info(f"Received response activity: {response.type} - {response.id}")
            if verbose:
                out.json(response.model_dump())
            out.newline()
