from __future__ import annotations

import sys
from io import StringIO
from threading import Lock, to_thread, Thread
import asyncio

from aiohttp import ClientSession
from aiohttp.web import Application, Request, Response, run_app

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)

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
        self._server_thread: Optional[Thread] = None

        self._app.router.add_post(
            "/v3/conversations/{path:.*}",
            self._handle_conversation
        )

    @property
    def service_endpoint(self) -> str:
        return self._service_endpoint
    
    def start(self) -> None:
        run_app(self._app, host=self._host, port=self._port)

    async def __aenter__(self) -> ResponseClient:
        if self._server_thread:
            raise RuntimeError("ResponseClient is already running.")
        
        self._prev_stdout = sys.stdout
        sys.stdout = StringIO()
        self._server_thread = Thread(target=self.start)
        self._server_thread.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if not self._server_thread:
            raise RuntimeError("ResponseClient is not running.")
        if self._prev_stdout is not None:
            sys.stdout = self._prev_stdout

        self._server_thread.join()
        self._server_thread = None

    async def _handle_conversation(self, request: Request) -> Response:
        try:
            body = await request.text()
            activity = Activity.model_validate(body)

            conversation_id = activity.conversation.id if activity.conversation else None

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

    async def _handle_streamed_activity(self, activity: Activity, *args, **kwargs) -> bool:
        raise NotImplementedError("_handle_streamed_activity is not implemented yet.")
