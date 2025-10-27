from typing import TypeVar
from threading import Thread

import aiohttp.web

AppT = TypeVar('AppT', bound=aiohttp.web.Application)

class ApplicationRunner:
    def __init__(self, app: AppT):
        self._app = app
        self._thread = None

    async def _start_server(self) -> None:
        runner = aiohttp.web.AppRunner(self._app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, 'localhost', 8080)
        await site.start()

    async def __aenter__(self) -> None:

        if self._thread:
            raise RuntimeError("Server is already running")
        
        self._thread = Thread(target=self._start_server, daemon=True)
        self._thread.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:

        if self._thread:
            
            if isinstance(self._app, aiohttp.web.Application):
                await self._app.shutdown()

            self._thread.join()
            self._thread = None
        else:
            raise RuntimeError("Server is not running")