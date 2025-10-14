# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import json
import requests
from typing import Callable, Awaitable, Any

def create_payload_sender(payload: dict[str, Any]) -> Callable[..., Awaitable[None]]:

    JWT_TOKEN = os.environ.get("JWT_TOKEN")
    ENDPOINT = "http://localhost:3978/api/messages"
    HEADERS = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    async def payload_sender() -> Any:

        response = requests.post(
            ENDPOINT,
            data=payload,
            headers=HEADERS
        )
        return response.content

    return payload_sender