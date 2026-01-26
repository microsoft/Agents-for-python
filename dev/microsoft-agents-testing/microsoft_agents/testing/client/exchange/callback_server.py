# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, AsyncContextManager

from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)

from .exchange import Exchange
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
    

class AiohttpCallbackServer(CallbackServer):
    """A test server that collects Activities sent to it."""

    def __init__(self, port: int = 9873):
        """Initializes the response server.

        :param port: The port number on which the server will listen.
        """
        self._port = port

        self._app: Application = Application()
        self._app.router.add_post("/v3/conversations/{path:.*}", self._handle_request)
        
        self._transcript: Transcript | None = None

    @property
    def service_endpoint(self) -> str:
        """Returns the service endpoint URL of the response server."""
        return f"http://localhost:{self._port}/v3/conversations/"

    @asynccontextmanager
    async def listen(self, transcript: Transcript | None = None) -> AsyncIterator[Transcript]:
        """Starts the callback server and yields a Transcript.

        :param transcript: An optional Transcript to collect incoming Activities.
        If None, a new Transcript will be created.
        :yield: A Transcript that collects incoming Activities.
        :raises: RuntimeError if the server is already listening.
        """

        if self._transcript is not None:
            raise RuntimeError("Response server is already listening for responses.")
        
        self._transcript = transcript or Transcript()

        async with TestServer(self._app, host="localhost", port=self._port):
            yield self._transcript

        self._transcript = None
    
    async def _handle_request(self, request: Request) -> Response:
        """Handles incoming POST requests and collects Activities.
        
        :param request: The incoming HTTP request.
        :return: An HTTP response indicating success or failure.
        :rtype: Response
        :raises: Exception if the request cannot be processed.
        """

        try:
            data = await request.json()
            activity = Activity.model_validate(data)

            exchange = Exchange(responses=[activity])

            if activity.type != ActivityTypes.typing:
                pass

            response = Response(
                status=200,
                content_type="application/json",
                text='{"message": "Activity received"}',
            )
        except Exception as e:
            if not Exchange.is_allowed_exception(e):
                raise e
            
            exchange = Exchange(error=str(e))
            response = Response(
                status=500,
                text=str(e)
            )
        
        self._transcript.record(exchange)
        return response