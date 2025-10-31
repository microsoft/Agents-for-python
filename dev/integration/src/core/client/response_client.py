from __future__ import annotations

import sys
from io import StringIO
from threading import Lock

from aiohttp import ClientSession
from aiohttp.web import Application, Request, Response

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
)

class ResponseClient:
    
    def __init__(
        self,
        service_endpoint: str = "http://localhost:9873"
    ):
        self._app: Application = Application()
        self._prev_stdout = None
        self._service_endpoint = service_endpoint
        self._activities_list = []
        self._activities_list_lock = Lock()

        self._app.router.add_post(
            "/v3/conversations/{path:.*}",
            self._handle_conversation
        )

    @property
    def service_endpoint(self) -> str:
        return self._service_endpoint

    def __aenter__(self) -> ResponseClient:
        self._prev_stdout = sys.stdout
        sys.stdout = StringIO()
        return self
    
    def __aexit__(self, exc_type, exc, tb):
        if self._prev_stdout is not None:
            sys.stdout = self._prev_stdout

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
                    async with ClientSession() as session:
                        async with session.post(
                            f"{self._service_endpoint}/v3/conversations/{conversation_id}/activities",
                            json=activity.model_dump()
                        ) as resp:
                            resp_text = await resp.text()
                            return Response(status=resp.status, text=resp_text)
                return Response(status=200, text="Activity received")
        except Exception as e:
            return Response(status=500, text=str(e))

    async def _handle_streamed_activity(self, activity: Activity, *args, **kwargs) -> bool:
        raise NotImplementedError("_handle_streamed_activity is not implemented yet.")