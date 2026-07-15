# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transport layer for agent communication.

This module provides the networking infrastructure for sending activities
to agents and receiving responses, including:

- Sender: Abstract interface for sending activities
- CallbackServer: Abstract interface for receiving async responses
- Transcript/Exchange: Recording of request-response pairs
- Aiohttp implementations of the above interfaces
"""

from .aiohttp_callback_server import AiohttpCallbackServer
from .aiohttp_sender import AiohttpSender
from .callback_server import CallbackServer
from .sender import Sender
from .transcript import (
    Transcript,
    Exchange,
)

__all__ = [
    "AiohttpCallbackServer",
    "AiohttpSender",
    "CallbackServer",
    "Sender",
    "Transcript",
    "Exchange"
]