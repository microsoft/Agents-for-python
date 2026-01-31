# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from abc import ABC, abstractmethod

from .transcript import Transcript

class CallbackServer(ABC):
    """A test server that collects Activities sent to it."""
    
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
    