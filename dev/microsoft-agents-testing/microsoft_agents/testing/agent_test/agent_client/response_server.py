from threading import Lock
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from aiohttp.web import Application, Request, Response
from aiohttp.test_utils import TestServer

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)

class ResponseServer:

    def __init__(self, host: str = "localhost", port: int = 9873):

        super().__init__(Application())

        service_endpoint = f"{host}:{port}/"
        if "http" not in service_endpoint:
            service_endpoint = "http://" + service_endpoint

        self._service_endpoint = service_endpoint

        self._responses = []
        self._lock = Lock()

        self._app.router.add_post("/v3/conversations/{path:.*}", self._handle_request)

    @asynccontextmanager
    async def run(self) -> AsyncContextManager[TestServer]:
        async with TestServer(self._app, host="localhost", port=9873) as server:
            yield server

    def _handle_request(self, request: Request) -> Response:
        return Response(text="OK")
    
    @property
    def service_endpoint(self) -> str:
        return self._service_endpoint
    
    def _add(self, activity: Activity) -> None:
        with self._lock:
            self._responses.append(activity)
    
    async def _handle_request(self, request: Request) -> Response:
        try:
            data = await request.json()
            activity = Activity.model_validate(data)

            self._add(activity)
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

    def pop(self) -> list[Activity]:
        with self._lock:
            activities = self._responses
            self._responses = []
        return activities