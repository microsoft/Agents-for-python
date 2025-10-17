import json
import logging
from datetime import datetime, timezone

import click

from .payload_sender import create_payload_sender
from .executor import Executor, CoroutineExecutor, ThreadExecutor
from .aggregated_results import AggregatedResults
from .config import BenchmarkConfig

LOG_FORMAT = "%(asctime)s: %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, datefmt="%H:%M:%S")

BenchmarkConfig.load_from_env()


@click.command()
@click.option(
    "--payload_path", "-p", default="./payload.json", help="Path to the payload file."
)
@click.option("--num_workers", "-n", default=1, help="Number of workers to use.")
@click.option(
    "--async_mode",
    "-a",
    is_flag=True,
    help="Run coroutine workers rather than thread workers.",
)
def main(payload_path: str, num_workers: int, async_mode: bool):
    """Main function to run the benchmark."""

    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    func = create_payload_sender(payload)

    executor: Executor = CoroutineExecutor() if async_mode else ThreadExecutor()

    start_time = datetime.now(timezone.utc).timestamp()
    results = executor.run(func, num_workers=num_workers)
    end_time = datetime.now(timezone.utc).timestamp()

    agg = AggregatedResults(results)
    agg.display(start_time, end_time)
    agg.display_timeline()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
