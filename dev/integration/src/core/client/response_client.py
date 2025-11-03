from __future__ import annotations

import sys
from io import StringIO
from typing import Optional
from threading import Lock, Thread, Event
import asyncio

from aiohttp import ClientSession
from aiohttp.web import Application, Request, Response, run_app
from aiohttp.web_runner import AppRunner, TCPSite

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
        self._server_thread: Optional[Thread] = None
        self._shutdown_event = Event()
        self._runner: Optional[AppRunner] = None
        self._site: Optional[TCPSite] = None

        self._app.router.add_post(
            "/v3/conversations/{path:.*}",
            self._handle_conversation
        )

        self._app_runner = AiohttpRunner(self._app)

    @property
    def service_endpoint(self) -> str:
        return self._service_endpoint
    
    def start(self) -> None:
        """Start the server in the current thread"""
        async def _run_server():
            self._runner = AppRunner(self._app)
            await self._runner.setup()
            self._site = TCPSite(self._runner, self._host, self._port)
            await self._site.start()
            
            # Wait for shutdown signal
            while not self._shutdown_event.is_set():
                await asyncio.sleep(0.1)
            
            # Cleanup
            await self._site.stop()
            await self._runner.cleanup()
        
        # Run the server
        asyncio.run(_run_server())

    async def _shutdown(self, request: Request) -> Response:
        """Handle shutdown request by setting the shutdown event"""
        self._shutdown_event.set()
        return Response(status=200, text="Shutdown initiated")

    async def __aenter__(self) -> ResponseClient:
        if self._server_thread:
            raise RuntimeError("ResponseClient is already running.")
        
        self._prev_stdout = sys.stdout
        sys.stdout = StringIO()
        self._shutdown_event.clear()
        self._server_thread = Thread(target=self.start)
        self._server_thread.start()
        
        # Wait a bit for the server to start
        await asyncio.sleep(0.2)
        return self

    async def _stop_server(self):
        if not self._server_thread:
            raise RuntimeError("ResponseClient is not running.")
        if self._prev_stdout is not None:
            sys.stdout = self._prev_stdout

        try:
            async with ClientSession() as session:
                async with session.get(f"http://{self._host}:{self._port}/shutdown") as response:
                    pass  # Just trigger the shutdown
        except Exception:
            pass  # Ignore errors during shutdown request
        
        # Set shutdown event as fallback
        self._shutdown_event.set()
        
        # Wait for the server thread to finish
        self._server_thread.join(timeout=5.0)
        self._server_thread = None

    async def _handle_conversation(self, request: Request) -> Response:
        try:
            data = await request.json()
            activity = Activity.model_validate(data)

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
    
    async def pop(self) -> list[Activity]:
        with self._activities_list_lock:
            activities = self._activities_list[:]
            self._activities_list.clear()
        return activities