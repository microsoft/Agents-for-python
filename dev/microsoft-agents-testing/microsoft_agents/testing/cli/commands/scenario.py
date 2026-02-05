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
    pass

@scenario.command("list")
@click.argument("pattern", default="*")
@pass_output
def scenario_list(out: Output, pattern: str) -> None:
    """List registered test scenarios matching a pattern."""
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
    """Run a specified test scenario."""
    if isinstance(scenario, ExternalScenario):
        out.error("Running an ExternalScenario is not supported in this command. Please use specific commands designed for interaction, such as 'chat' or 'post'.")
        raise click.Abort()
    
    out.newline()
    out.info("🚀 Scenario is running...")
    out.info("Press Ctrl+C to stop.")
    out.newline()
    
    try:
        async with scenario.run() as factory:
            # Block forever until KeyboardInterrupt
            await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    
    out.newline()
    out.success("Scenario stopped.")

# yes, I did ask Copilot to make this look pretty
@scenario.command("chat")
@async_command
@pass_output
@with_scenario
async def chat(out: Output, scenario: Scenario) -> None:
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
async def post(out: Output, scenario: Scenario, message: str | None, json_file, wait: float) -> None:
    
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
