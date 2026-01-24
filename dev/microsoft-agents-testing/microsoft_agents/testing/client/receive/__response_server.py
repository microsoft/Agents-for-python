# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)

from .response_collector import ResponseCollector

class ResponseServer:
    """A test server that collects Activities sent to it."""

    def __init__(self, port: int = 9873):
        """Initializes the response server.

        :param port: The port on which the server will listen.
        """
        self._port = port

        self._collector: ResponseCollector | None = None

        self._app: Application = Application()
        self._app.router.add_post("/v3/conversations/{path:.*}", self._handle_request)

    @asynccontextmanager
    async def run(self) -> AsyncIterator[ResponseCollector]:

    @asynccontextmanager
    async def listen(self) -> AsyncIterator[ResponseCollector]:
        """Starts the response server and yields a ResponseCollector.
        
        Only one listener can be active at a time.

        :yield: A ResponseCollector that collects incoming Activities.
        :raises: RuntimeError if the server is already listening.
        """

        if self._collector:
            raise RuntimeError("Response server is already listening for responses.")
        
        self._collector = ResponseCollector()

        async with TestServer(self._app, host="localhost", port=self._port):
            yield self._collector

        self._collector = None
    
    @property
    def service_endpoint(self) -> str:
        """Returns the service endpoint URL of the response server."""
        return f"http://localhost:{self._port}/v3/conversations/"
    
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

            if self._collector: self._collector.add(activity)
            if activity.type != ActivityTypes.typing:
                pass

            return Response(
                status=200,
                content_type="application/json",
                text='{"message": "Activity received"}',
            )
        except Exception as e:
            return Response(
                status=500,
                text=str(e)
            )