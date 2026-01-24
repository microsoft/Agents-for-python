from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from .response_receiver import ResponseReceiver

class ResponseServer(ABC):
    """Abstract base for a server that receives responses."""

    @abstractmethod
    @asynccontextmanager
    async def run(self) -> AsyncIterator[ResponseReceiver]:
        """Starts the response server and yields a ResponseReceiver."""
        ...