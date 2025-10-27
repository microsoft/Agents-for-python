from __future__ import annotations

from typing import Protocol

class ResponseClientProtocol(Protocol):

    async def __aenter__(self) -> ResponseClientProtocol:
        ...

    async def __aexit__(self, exc_type, exc, tb) -> None:
        ...