# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""CallbackServer - Abstract interface for receiving agent responses.

Defines the protocol for servers that receive asynchronous activity
responses from agents (e.g., when using callback URLs).
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from abc import ABC, abstractmethod

from .transcript import Transcript


class CallbackServer(ABC):
    """Abstract server that receives Activities sent by agents.
    
    Implementations start an HTTP server that agents can post responses to,
    collecting them into a Transcript for later assertion.
    """
    
    @abstractmethod
    @asynccontextmanager
    async def listen(self, transcript: Transcript | None = None) -> AsyncIterator[Transcript]:
        """Starts the response server and yields a Transcript.

        :param transcript: An optional Transcript to collect incoming Activities.
        If None, a new Transcript will be created.

        :yield: A Transcript that collects incoming Activities.
        :raises: RuntimeError if the server is already listening.
        """
        ...
    