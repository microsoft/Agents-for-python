from __future__ import annotations

import sys
from io import StringIO
from threading import Lock
import asyncio

from aiohttp.web import Application, Request, Response

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)

from ..aiohttp import AiohttpRunner


class ResponseClient:

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9873,
    ):
        self._app: Application = Application()
        self._prev_stdout = None
        service_endpoint = f"{host}:{port}"
        self._host = host
        self._port = port
        if "http" not in service_endpoint:
            service_endpoint = f"http://{service_endpoint}"
        self._service_endpoint = service_endpoint
        self._activities_list = []
        self._activities_list_lock = Lock()

        self._app.router.add_post(
            "/v3/conversations/{path:.*}", self._handle_conversation
        )

        self._app_runner = AiohttpRunner(self._app, host, port)

    @property
    def service_endpoint(self) -> str:
        return self._service_endpoint

    async def __aenter__(self) -> ResponseClient:
        self._prev_stdout = sys.stdout
        sys.stdout = StringIO()

        await self._app_runner.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._prev_stdout is not None:
            sys.stdout = self._prev_stdout

        await self._app_runner.__aexit__(exc_type, exc_val, exc_tb)

    async def _handle_conversation(self, request: Request) -> Response:
        try:
            data = await request.json()
            activity = Activity.model_validate(data)

            # conversation_id = (
            #     activity.conversation.id if activity.conversation else None
            # )

            with self._activities_list_lock:
                self._activities_list.append(activity)

            if any(map(lambda x: x.type == "streaminfo", activity.entities or [])):
                await self._handle_streamed_activity(activity)
                return Response(status=200, text="Stream info handled")
            else:
                if activity.type != ActivityTypes.typing:
                    await asyncio.sleep(0.1)  # Simulate processing delay
                return Response(status=200, text="Activity received")
        except Exception as e:
            return Response(status=500, text=str(e))

    async def _handle_streamed_activity(
        self, activity: Activity, *args, **kwargs
    ) -> bool:
        raise NotImplementedError("_handle_streamed_activity is not implemented yet.")

    async def pop(self) -> list[Activity]:
        with self._activities_list_lock:
            activities = self._activities_list[:]
            self._activities_list.clear()
        return activities
