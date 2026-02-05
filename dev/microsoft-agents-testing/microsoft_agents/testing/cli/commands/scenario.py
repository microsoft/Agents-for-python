import click

from microsoft_agents.activity import Activity
from microsoft_agents.testing.core import Scenario
from microsoft_agents.testing.scenario_registry import scenario_registry

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

# @scenario.command("run")
# @async_command
# @with_scenario
# async def scenario_run(scenario_ctx: ScenarioContext) -> None:
#     """Run a specified test scenario."""
#     async with scenario.client() as client:
#         # todo -> blocking interaction for now
#         pass

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
    async with scenario.client() as client:
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
    out.error("Transcript of the conversation: TODO")

# @scenario.command("post")
# @async_command
# @pass_output
# @with_scenario
# async def post(out: Output, scenario: Scenario, payload: str | dict, wait: float) -> None:
        

#     async with scenario.client() as client:
        
#         activity_or_str: Activity | str
#         if isinstance(payload, str):
#             activity_or_str = payload
#         else:
#             assert isinstance(payload, dict)
#             activity_or_str = client.template.create(payload)

#         await client.send(activity_or_str, wait=wait)

#     transcript = client.transcript
#     out.error("Transcript of the conversation: TODO")