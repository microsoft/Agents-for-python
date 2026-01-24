# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional
import asyncio

from aiohttp import ClientSession
from aiohttp.web import Application, Request, Response
from aiohttp.web_runner import AppRunner, TCPSite

from ..application_runner import ApplicationRunner


class AiohttpAsyncRunner(ApplicationRunner):
    """A runner for aiohttp applications."""

    def __init__(self, app: Application, host: str = "localhost", port: int = 8000):
        assert isinstance(app, Application)
        super().__init__(app)

        url = f"{host}:{port}"
        self._host = host
        self._port = port
        if "http" not in url:
            url = f"http://{url}"
        self._url = url

        self._app.router.add_get("/shutdown", self._shutdown_route)

        self._server_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._runner: Optional[AppRunner] = None
        self._site: Optional[TCPSite] = None

    @property
    def url(self) -> str:
        return self._url

    async def _start_server(self) -> None:
        assert isinstance(self._app, Application)

        self._runner = AppRunner(self._app)
        await self._runner.setup()
        self._site = TCPSite(self._runner, self._host, self._port)
        await self._site.start()

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Cleanup
        await self._site.stop()
        await self._runner.cleanup()

    async def __aenter__(self):
        if self._server_task:
            raise RuntimeError("AiohttpRunner is already running.")

        self._shutdown_event.clear()

        # Create a background task instead of a thread
        self._server_task = asyncio.create_task(self._start_server())

        # Wait a moment to ensure the server starts
        await asyncio.sleep(0.5)

        return self

    async def _stop_server(self):
        try:
            async with ClientSession() as session:
                async with session.get(
                    f"http://{self._host}:{self._port}/shutdown"
                ) as response:
                    pass  # Just trigger the shutdown
        except Exception:
            pass  # Ignore errors during shutdown request

        # Set shutdown event as fallback
        self._shutdown_event.set()

    async def _shutdown_route(self, request: Request) -> Response:
        """Handle shutdown request by setting the shutdown event"""
        self._shutdown_event.set()
        return Response(status=200, text="Shutdown initiated")

    async def __aexit__(self, exc_type, exc, tb):
        if not self._server_task:
            raise RuntimeError("AiohttpRunner is not running.")

        await self._stop_server()

        # Wait for the server task to complete
        try:
            await asyncio.wait_for(self._server_task, timeout=5.0)
        except asyncio.TimeoutError:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass

        self._server_task = None
