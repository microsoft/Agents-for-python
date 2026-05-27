# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import click

from datetime import timedelta
from dataclasses import dataclass

from microsoft_agents.activity import Activity
from microsoft_agents.testing.cli.core import (
    async_command,
    pass_output,
    Output,
    with_scenario
)
from microsoft_agents.testing.core import (
    Exchange,
    Scenario
)

from .scenario_group import scenario_group
from ._utils import load_activity

@dataclass
class RunResult:
    """Represents the result of a load test run."""

    latency: timedelta | None
    error: bool
    error_message: str | None

async def run_load_test(scenario: Scenario, activity: Activity, num: int, timeout: float) -> list[RunResult | None]:
    """Run a load test with the given scenario, activity, and parameters."""

    results: list[RunResult | None] = [None] * num
    seen: list[bool] = [False] * num

    async with scenario.run() as client_factory:

        async def send_activity(run_id: int):
            """Send an activity and record the result."""
            seen[run_id] = True
            try:
                client = await client_factory()

                exchange: Exchange
                async with asyncio.timeout(timeout / 1000):
                    exchange = (await client.ex_send_expect_replies(activity))[-1]

                results[run_id] = RunResult(
                    latency=exchange.latency,
                    error=exchange.is_error,
                    error_message=exchange.error
                )
            except asyncio.TimeoutError:
                results[run_id] = RunResult(
                    latency=timedelta(milliseconds=timeout),
                    error=True,
                    error_message="Request timed out"
                )
            except Exception as e:
                results[run_id] = RunResult(
                    latency=None,
                    error=True,
                    error_message=str(e)
                )

        await asyncio.gather(
            *[send_activity(i) for i in range(num)]
        )

    return results

def show_results(results: list[RunResult | None], out: Output) -> None:
    """Display the results of a load test."""

    latencies: list[timedelta] = []
    error_ids: list[int] = []
    missing_ids: list[int] = []

    for i, result in enumerate(results):
        if result is None or result.latency is None:
            out.error(f"Request {i} failed to complete.")
            missing_ids.append(i)
        elif result.error:
            out.error(f"Request {i} failed with error: {result.error_message}")
            error_ids.append(i)
            latencies.append(result.latency)
        else:
            latencies.append(result.latency)
    
    out.info(f"Completed {len(latencies)} requests.")
    if error_ids:
        out.info(f"Failed {len(error_ids)} requests.")
    if missing_ids:
        out.info(f"Missing {len(missing_ids)} requests.")

    if latencies:
        out.info(f"Average latency: {sum(latencies, timedelta()).total_seconds() / len(latencies) * 1000:.2f} ms")
        out.info(f"Minimum latency: {min(latencies).total_seconds() * 1000:.2f} ms")
        out.info(f"Maximum latency: {max(latencies).total_seconds() * 1000:.2f} ms")
        out.info(f"90th percentile latency: {sorted(latencies)[int(len(latencies) * 0.9)].total_seconds() * 1000:.2f} ms")
        
        


@scenario_group.command("load")
@async_command
@pass_output
@with_scenario
@click.option("--message", "-m", required=False, help="Text message to send to the agent.")
@click.option("--json_file", "-j", required=False, type=click.File("rb"), help="JSON activity to send to the agent.")
@click.option("--num", "-n", required=True, type=int, help="Number of concurrent requests to make.")
@click.option("--timeout", "-t", default=5000, help="Milliseconds to wait for a response before timing out.")
async def load(out: Output, scenario: Scenario, message: str | None, json_file, num: int, timeout: float) -> None:
    """Run a concurrent load test against an agent and report latency statistics.

    Sends the same message or activity to the agent ``--num`` times concurrently
    and prints per-request results along with average, min, max, and p90 latencies.

    Provide either a text message via ``--message`` or a JSON activity via ``--json_file``.

    :param out: CLI output helper.
    :param scenario: The resolved Scenario instance.
    :param message: Plain text message to send to each concurrent request.
    :param json_file: File handle for a JSON activity payload to send to each request.
    :param num: Number of concurrent requests to send.
    :param timeout: Milliseconds to wait per request before treating it as a timeout error.
    """
    
    activity = load_activity(message, json_file, out)

    results: list[RunResult | None] = await run_load_test(scenario, activity, num, timeout)

    show_results(results, out)