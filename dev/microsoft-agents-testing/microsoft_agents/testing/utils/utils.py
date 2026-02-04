import functools

from microsoft_agents.testing.core import ExternalScenario

from ..aiohttp_scenario import AiohttpScenario, AgentEnvironment
from ..scenario_registry.scenario_registry import scenario_registry


@functools.singledispatch
def register_aiohttp_scenario(
    name: str,
    url: str,
    *,
    description: str = "",
) -> None:
    """Register an ExternalScenario using an aiohttp endpoint URL.
    
    :param name: The unique name for the scenario.
    :param url: The URL of the agent's message endpoint.
    :param description: Optional description of the scenario.
    
    Example::
    
        from microsoft_agents.testing import scenario_registry
        register_aiohttp_scenario(
            "local.echo",
            "http://localhost:3978/api/messages",
            description="Local echo agent",
        )
    """
    scenario = ExternalScenario(url)
    scenario_registry.register(
        name,
        scenario,
        description=description,
    )

@register_aiohttp_scenario.register
def _(name: str, init_agent: callable, **kwargs) -> None:
    """Register an AiohttpScenario using an init_agent function.
    
    :param name: The unique name for the scenario.
    :param init_agent: Async function to initialize the agent with handlers.
    :param kwargs: Additional keyword arguments for AiohttpScenario.
    
    Example::
    
        from microsoft_agents.testing import scenario_registry
        async def init_agent(env: AgentEnvironment):
            @env.agent_application.activity(ActivityTypes.message)
            async def handler(context, state):
                await context.send_activity(f"Echo: {context.activity.text}")
        
        register_aiohttp_scenario(
            "local.echo",
            init_agent,
            description="Local echo agent",
        )
    """
    scenario = AiohttpScenario(init_agent, **kwargs)
    scenario_registry.register(
        name,
        scenario,
        description=kwargs.get("description", ""),
    )