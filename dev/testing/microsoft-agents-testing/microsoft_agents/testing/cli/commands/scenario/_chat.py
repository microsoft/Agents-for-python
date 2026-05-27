# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import click

from microsoft_agents.testing.cli.core import (
    async_command,
    pass_output,
    Output,
    with_scenario,
)
from microsoft_agents.testing.core import Scenario

from .scenario_group import scenario_group

@scenario_group.command("chat")
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