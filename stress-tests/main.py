import json
import logging
import argparse
import requests
from typing import Callable, Awaitable, Any
from concurrent.futures import ThreadPoolExecutor

import click

format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)


def payload_sender_func(payload: dict[str, Any]) -> Callable[..., Awaitable[None]]:
    async def payload_sender() -> None:
        requests.post(
            "http://localhost:3978/api/messages",
            json=payload
        )
    return payload_sender

def test(
    func: Callable[..., Awaitable[None]],
    num_threads: int = 1,
) -> None:
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(func) for _ in range(num_threads)]
        for future in futures:
            future.result()


@click.command()
@click.option("--payload_path", default="./payload.json", help="Path to the payload file.")
@click.option("--num-threads", default=1, help="Number of threads to use.")
def main(
    payload_path: str,
    num_threads: int,
):
    
    with open(payload_path, "r") as f:
        payload = json.load(f)

    func = payload_sender_func(payload)

    test(func, num_threads=num_threads)