from src.core import ApplicationRunner

class SimpleRunner(ApplicationRunner):
    def _start_server(self) -> None:
        self._app["running"] = True

    @property
    def app(self):
        return self._app

class OtherSimpleRunner(SimpleRunner):
    def _stop_server(self) -> None:
        self._app["running"] = False