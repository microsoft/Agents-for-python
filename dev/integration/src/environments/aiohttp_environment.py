
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
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

from .application_runner import ApplicationRunner
from .environment import Environment

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

    async def init_env(self, environ_dict: dict) -> None:
        environ_dict = environ_dict or {}

        agents_sdk_config = load_configuration_from_env(environ_dict)

        storage = MemoryStorage()
        connection_manager = MsalConnectionManager(**agents_sdk_config)
        adapter = CloudAdapter(connection_manager=connection_manager)
        authorization = Authorization(storage, connection_manager, **agents_sdk_config)

        agent_application = AgentApplication[TurnState](
            storage=storage,
            adapter=adapter,
            authorization=authorization,
            **agents_sdk_config
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
        APP["agent_configuration"] = self.connections.get_default_connection()
        APP["agent_app"] = self.agent_application
        APP["adapter"] = self.adapter

        return ApplicationRunner(APP)