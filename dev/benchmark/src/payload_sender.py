# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import requests
from typing import Callable, Awaitable, Any

from .config import BenchmarkConfig
from .generate_token import generate_token_from_env


def create_payload_sender(
    payload: dict[str, Any], timeout: int = 60
) -> Callable[..., Awaitable[Any]]:
    """Create a payload sender function that sends the given payload to the configured endpoint.

    :param payload: The payload to be sent.
    :param timeout: The timeout for the request in seconds.
    :return: A callable that sends the payload when invoked.
    """

    token = generate_token_from_env()
    endpoint = BenchmarkConfig.AGENT_URL
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def payload_sender() -> Any:
        response = await asyncio.to_thread(
            requests.post, endpoint, headers=headers, json=payload, timeout=timeout
        )
        return response.content

    return payload_sender
