from abc import ABC, abstractmethod
from typing import Any, Optional
from threading import Thread

class ApplicationRunner(ABC):
    """Base class for application runners."""
    
    def __init__(self, app: Any):
        self._app = app
        self._thread: Optional[Thread] = None

    @abstractmethod
    def _start_server(self) -> None:
        raise NotImplementedError("Start server method must be implemented by subclasses")
        
    def _stop_server(self) -> None:
        pass

    async def __aenter__(self) -> None:

        if self._thread:
            raise RuntimeError("Server is already running")
        
        self._thread = Thread(target=self._start_server, daemon=True)
        self._thread.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:

        if self._thread:
            self._stop_server()

            self._thread.join()
            self._thread = None
        else:
            raise RuntimeError("Server is not running")