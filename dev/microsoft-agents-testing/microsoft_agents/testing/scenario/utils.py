from typing import Awaitable, Callable

from .aiohttp_scenario import AiohttpScenario, AgentEnvironment
from .scenario import ScenarioConfig

def aiohttp_scenario(cls, config: ScenarioConfig | None = None, use_jwt_middleware: bool = True):
    def decorator(
        init_agent: Callable[[AgentEnvironment], Awaitable[None]]
    ) -> AiohttpScenario:
        return cls(
            init_agent=init_agent,
            config=config,
            use_jwt_middleware=use_jwt_middleware,
        )
    return decorator