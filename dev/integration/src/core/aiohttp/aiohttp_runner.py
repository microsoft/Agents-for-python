from typing import Optional
from typing import Optional
from threading import Thread, Event
import asyncio

from aiohttp.web import Application, Request, Response
from aiohttp.web_runner import AppRunner, TCPSite

from ..application_runner import ApplicationRunner

class AiohttpRunner(ApplicationRunner):
    """A runner for aiohttp applications."""
    
    def __init__(self, app: Application):
        assert isinstance(app, Application)
        super().__init__(app)

        self._app.router.add_get(
            "/shutdown",
            self._shutdown
        )

        self._server_thread: Optional[Thread] = None
        self._shutdown_event = Event()
        self._runner: Optional[AppRunner] = None
        self._site: Optional[TCPSite] = None


    async def _start_server(self) -> None:
        try:
            assert isinstance(self._app, Application)
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
        except Exception as error:
            raise error
        
    async def _stop_server(self) -> None:
        pass

    async def _shutdown(self, request: Request) -> Response:
        """Handle shutdown request by setting the shutdown event"""
        self._shutdown_event.set()
        return Response(status=200, text="Shutdown initiated")
    
    async def __aexit__(self, exc_type, exc, tb):
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