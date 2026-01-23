import json

import click

from microsft_agents.testing.agent_test import 

from microsoft_agents.testing.cli.common import (
    Executor,
    CoroutineExecutor,
    ThreadExecutor,
    create_payload_sender,
)

from microsoft_agents.testing.agent_test import (
    AgentScenarioConfig,
    ExternalAgentScenario,
)


@click.command()
@click.option(
    "--payload_path", "-p", default="./payload.json", help="Path to the payload file."
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.option(
    "--async_mode",
    "-a",
    is_flag=True,
    help="Run coroutine workers rather than thread workers.",
)
def post(payload_path: str, async_mode: bool):
    """Send an activity to an agent."""

    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    template = ActivityTemplate(payload)

    scenario = ExternalAgentScenario()

    payload_sender = create_payload_sender(payload)

    executor: Executor = CoroutineExecutor() if async_mode else ThreadExecutor()

    result = executor.run(payload_sender)[0]

    status = "Success" if result.success else "Failure"
    print(
        f"Execution ID: {result.exe_id}, Duration: {result.duration:.4f} seconds, Status: {status}"
    )
    print(result.result)
