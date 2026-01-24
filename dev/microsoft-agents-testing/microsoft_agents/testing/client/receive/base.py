from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from microsoft_agents.activity import Activity

class ResponseReceiver(ABC):
    """Abstract base for receiving agent responses."""
    
    @property
    @abstractmethod
    def service_endpoint(self) -> str:
        """The endpoint URL agents should send responses to."""
        ...
    
    @abstractmethod
    def get_all(self) -> list[Activity]:
        """Get all responses received so far."""
        ...
    
    @abstractmethod
    def get_new(self) -> list[Activity]:
        """Get responses since last call (pops from internal queue)."""
        ...

    @abstractmethod
    def child(self) -> ResponseReceiver:
        ...

class ResponseServer(ABC):
    """Abstract base for a server that receives responses."""

    @abstractmethod
    @asynccontextmanager
    async def run(self) -> AsyncIterator[ResponseReceiver]:
        """Starts the response server and yields a ResponseReceiver."""
        ...