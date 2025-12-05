import json
import logging
from datetime import datetime, timezone

import click

from microsoft_agents.testing.cli.common import (
    Executor,
    CoroutineExecutor,
    ThreadExecutor,
    create_payload_sender,
)

from .aggregated_results import AggregatedResults
from .output import output_results

LOG_FORMAT = "%(asctime)s: %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, datefmt="%H:%M:%S")


@click.command()
@click.option(
    "--payload_path", "-p", default="./payload.json", help="Path to the payload file."
)
@click.option("--num_workers", "-n", default=1, help="Number of workers to use.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.option(
    "--async_mode",
    "-a",
    is_flag=True,
    help="Run coroutine workers rather than thread workers.",
)
def benchmark(payload_path: str, num_workers: int, verbose: bool, async_mode: bool):
    """Command to run the benchmark."""

    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    payload_sender = create_payload_sender(payload)

    executor: Executor = CoroutineExecutor() if async_mode else ThreadExecutor()

    start_time = datetime.now(timezone.utc).timestamp()
    results = executor.run(payload_sender, num_workers=num_workers)
    end_time = datetime.now(timezone.utc).timestamp()
    if verbose:
        output_results(results)

    agg = AggregatedResults(results)
    agg.display(start_time, end_time)
    agg.display_timeline()
