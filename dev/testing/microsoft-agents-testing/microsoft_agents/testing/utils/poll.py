# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio

from typing import Callable

async def poll(condition: Callable[[], bool], timeout: float, interval: float = 0.1) -> None:
    """Polls a callable function until it returns or a timeout is reached."""

    if interval < 0:
        raise ValueError("Interval must be a non-negative number.")
    if timeout < interval:
        raise ValueError("Timeout must be greater than or equal to interval.")        

    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        if condition():
            return
        await asyncio.sleep(interval)
    raise TimeoutError("Polling timed out")