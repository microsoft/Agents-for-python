
from tkinter import E
from aiohttp.web import Request, Response, Application, run_app

from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process
)
from microsoft_agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    MemoryStorage,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

from ..core import (
    ApplicationRunner,
    Environment
)

class AiohttpRunner(ApplicationRunner):
    """A runner for aiohttp applications."""

    def _start_server(self) -> None:
        try:
            assert isinstance(self._app, Application)
            run_app(self._app, host="localhost", port=3978)
        except Exception as error:
            raise error
        
    def _stop_server(self) -> None:
        pass

class AiohttpEnvironment(Environment):
    """An environment for aiohttp-hosted agents."""

    async def init_env(self, environ_config: dict) -> None:
        environ_config = environ_config or {}

        self.config = load_configuration_from_env(environ_config)

        self.storage = MemoryStorage()
        self.connection_manager = MsalConnectionManager(**self.config)
        self.adapter = CloudAdapter(connection_manager=self.connection_manager)
        self.authorization = Authorization(self.storage, self.connection_manager, **self.config)

        self.agent_application = AgentApplication[TurnState](
            storage=self.storage,
            adapter=self.adapter,
            authorization=self.authorization,
            **self.agents_sdk_config
        )
    
    def create_runner(self) -> ApplicationRunner:
        
        async def entry_point(req: Request) -> Response:
            agent: AgentApplication = req.app["agent_app"]
            adapter: CloudAdapter = req.app["adapter"]
            return await start_agent_process(
                req,
                agent,
                adapter
            )

        APP = Application(middlewares=[jwt_authorization_middleware])
        APP.router.add_post("/api/messages", entry_point)
        APP["agent_configuration"] = self.connection_manager.get_default_connection()
        APP["agent_app"] = self.agent_application
        APP["adapter"] = self.adapter

        return AiohttpRunner(APP)