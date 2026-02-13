# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Scenario CLI commands.

Provides commands for listing, running, chatting, and posting to
agent test scenarios from the command line.
"""

import json
import asyncio

import click

from microsoft_agents.activity import Activity
from microsoft_agents.testing.core import Scenario, ExternalScenario
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.transcript_formatter import ActivityTranscriptFormatter

from ..core import (
    async_command,
    pass_output,
    Output,
    with_scenario,
)

@click.group()
def scenario():
    """Manage test scenarios."""


@scenario.command("list")
@click.argument("pattern", default="*")
@pass_output
def scenario_list(out: Output, pattern: str) -> None:
    """List registered test scenarios matching a pattern.

    :param out: CLI output helper.
    :param pattern: Glob-style pattern to filter scenario names.
    """
    matched_scenarios = scenario_registry.discover(pattern)

    out.newline()
    out.info(f"Matching scenarios to pattern '{pattern}':")
    if not matched_scenarios:
        out.info("No scenarios found matching the pattern.")
        return
    out.newline()

    for name, entry in matched_scenarios.items():
        out.info(f"\t{name}: {entry.description}")
    out.newline()

@scenario.command("run")
@async_command
@pass_output
@with_scenario
async def scenario_run(out: Output, scenario: Scenario) -> None:
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


@scenario.command("chat")
@async_command
@pass_output
@with_scenario
async def scenario_chat(out: Output, scenario: Scenario) -> None:
    """Interactive chat with an agent.
    
    Starts a REPL-style conversation where you can send messages and
    see the agent's responses in real-time.
    
    Examples:
    
        \b
        # Chat with an external agent
        mat chat --url http://localhost:3978/api/messages
        
        \b
        # Chat with an in-process agent
        mat chat --agent myproject.agents.echo
    """
    # Print welcome banner
    out.newline()
    click.secho("╔══════════════════════════════════════════════════════════════╗", fg="cyan")
    click.secho("║              🤖  Agent Chat Interface  🤖                    ║", fg="cyan")
    click.secho("╚══════════════════════════════════════════════════════════════╝", fg="cyan")
    out.newline()
    click.secho("  Type your message and press Enter to chat with the agent.", fg="white", dim=True)
    click.secho("  Type '/exit' or '/quit' to end the conversation.", fg="white", dim=True)
    click.secho("  ─" * 32, fg="cyan", dim=True)
    out.newline()

    async with scenario.client() as client:
        message_count = 0
        
        while True:
            # User input prompt with styling
            click.secho("You: ", fg="green", bold=True, nl=False)
            user_input = click.prompt("", prompt_suffix="")
            
            if user_input.lower() in ("/exit", "/quit"):
                break
            
            if not user_input.strip():
                click.secho("  (empty message, skipping...)", fg="yellow", dim=True)
                continue
            
            message_count += 1
            
            # Show thinking indicator
            click.secho("  ⏳ Agent is thinking...", fg="cyan", dim=True)
            
            try:
                replies = await client.send_expect_replies(user_input)
                
                # Clear the "thinking" line by moving up (optional, works in most terminals)
                click.echo("\033[A\033[K", nl=False)  # Move up and clear line
                
                if replies:
                    for reply in replies:
                        if reply.type == "message" and reply.text:
                            click.secho("Agent: ", fg="blue", bold=True, nl=False)
                            click.echo(reply.text)
                        elif reply.type == "typing":
                            # Skip typing indicators in output
                            pass
                        else:
                            # Show other activity types in debug style
                            click.secho(f"  [activity: {reply.type}]", fg="magenta", dim=True)
                else:
                    click.secho("  (no response from agent)", fg="yellow", dim=True)
                    
            except Exception as e:
                click.secho(f"  ❌ Error: {e}", fg="red")
            
            out.newline()
    
    # Print exit summary
    out.newline()
    click.secho("  ─" * 32, fg="cyan", dim=True)
    click.secho(f"  📊 Session Summary: {message_count} messages exchanged", fg="cyan")
    out.newline()
    out.success("Chat session ended. Goodbye!")
    out.newline()

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
