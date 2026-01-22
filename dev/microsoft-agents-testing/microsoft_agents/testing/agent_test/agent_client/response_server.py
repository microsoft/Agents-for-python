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

    def __init__(self, port: int = 9873):

        super().__init__(Application())

        self._service_endpoint = f"http://localhost:{port}/"
        self._port = port

        self._collector: ResponseCollector | None = None

        self._app.router.add_post("/v3/conversations/{path:.*}", self._handle_request)

    @asynccontextmanager
    async def listen(self) -> AsyncIterator[ResponseCollector]:

        if self._collector:
            raise RuntimeError("Response server is already listening for responses.")
        
        self._collector = ResponseCollector(filter)

        async with TestServer(self._app, host="localhost", port=self._port):
            yield self._collector

        self._collector = None
    
    @property
    def service_endpoint(self) -> str:
        return self._service_endpoint
    
    async def _handle_request(self, request: Request) -> Response:
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