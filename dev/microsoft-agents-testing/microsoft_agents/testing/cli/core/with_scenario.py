# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Decorator for CLI commands that interact with agents via scenarios.

Provides a unified way to handle both ExternalScenario (external agents)
and AiohttpScenario (in-process agents) in CLI commands.
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Any, TYPE_CHECKING

import click

from microsoft_agents.testing.core import (
    ExternalScenario,
    Scenario,
    ScenarioConfig,
    AgentClient,
)

if TYPE_CHECKING:
    from ..config import CLIConfig


class ScenarioContext:
    """Context object passed to commands using @with_scenario.
    
    Provides access to the scenario and client for agent interaction.
    
    Attributes:
        scenario: The active Scenario instance (ExternalScenario or AiohttpScenario).
        client: The AgentClient for sending messages to the agent.
        config: The CLI configuration.
        verbose: Whether verbose output is enabled.
    """
    
    def __init__(
        self,
        scenario: Scenario,
        client: AgentClient,
        config: "CLIConfig",
        verbose: bool = False,
    ) -> None:
        self.scenario = scenario
        self.client = client
        self.config = config
        self.verbose = verbose


def with_scenario(func: Callable) -> Callable:
    """Decorator for commands that can interact with agents via scenarios.
    
    This decorator adds options for specifying how to connect to an agent:
    - --url/-u: Connect to an external agent at the specified URL
    - --agent/-a: Run an in-process agent from the specified module path
    
    The decorated function receives a ScenarioContext as its first argument
    (after click.Context), providing access to the scenario and client.
    
    Example::
    
        @click.command()
        @click.pass_context
        @with_scenario
        @async_command
        async def chat(ctx: click.Context, scenario_ctx: ScenarioContext) -> None:
            client = scenario_ctx.client
            replies = await client.send_expect_replies("Hello!")
            for reply in replies:
                print(f"Agent: {reply.text}")
    
    The decorator supports two modes:
    
    1. External Agent Mode (--url):
       Uses ExternalScenario to connect to an agent running at the specified
       URL. This is the default mode when AGENT_URL is configured.
       
       Example: mat chat --url http://localhost:3978/api/messages
    
    2. In-Process Agent Mode (--agent):
       Uses AiohttpScenario to run the agent in-process. The --agent option
       specifies a Python module path containing an init_agent function.
       
       Example: mat chat --agent myproject.agents.echo
       
       The module must export an async function called `init_agent` that
       takes an AgentEnvironment and configures the agent handlers.
    """
    
    @click.option(
        "--url", "-u",
        "agent_url",
        default=None,
        help="URL of an external agent endpoint.",
    )
    @click.option(
        "--agent", "-a",
        "agent_module",
        default=None,
        help="Python module path for in-process agent (e.g., myproject.agents.echo).",
    )
    @wraps(func)
    async def wrapper(
        ctx: click.Context,
        agent_url: str | None,
        agent_module: str | None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        from ..config import CLIConfig
        from .output import Output
        
        config: CLIConfig = ctx.obj["config"]
        verbose: bool = ctx.obj.get("verbose", False)
        out = Output(verbose=verbose)
        
        # Determine which scenario to use
        scenario = _create_scenario(
            agent_url=agent_url,
            agent_module=agent_module,
            config=config,
            out=out,
        )
        
        # Run the scenario and execute the command
        async with scenario.client() as client:
            scenario_ctx = ScenarioContext(
                scenario=scenario,
                client=client,
                config=config,
                verbose=verbose,
            )
            return await func(ctx, scenario_ctx, *args, **kwargs)
    
    return wrapper


def _create_scenario(
    agent_url: str | None,
    agent_module: str | None,
    config: "CLIConfig",
    out: Any,
) -> Scenario:
    """Create the appropriate scenario based on the provided options.
    
    Priority:
    1. If --agent is provided, use AiohttpScenario with the specified module
    2. If --url is provided, use ExternalScenario with that URL
    3. If AGENT_URL is configured, use ExternalScenario with that URL
    4. Raise an error if no agent is specified
    """
    from microsoft_agents.testing import AiohttpScenario
    
    scenario_config = ScenarioConfig(
        env_file_path=config.env_path,
    )
    
    # In-process agent takes priority if specified
    if agent_module:
        init_agent = _load_agent_module(agent_module, out)
        out.debug(f"Using in-process agent from module: {agent_module}")
        return AiohttpScenario(init_agent, config=scenario_config)
    
    # External agent URL
    url = agent_url or config.agent_url
    if url:
        out.debug(f"Using external agent at: {url}")
        return ExternalScenario(url, config=scenario_config)
    
    # No agent specified
    out.error("No agent specified.")
    out.info("Provide --url for an external agent or --agent for an in-process agent.")
    out.info("Alternatively, set AGENT_URL in your .env file.")
    raise click.Abort()


def _load_agent_module(module_path: str, out: Any) -> Callable:
    """Load the init_agent function from the specified module.
    
    The module must export an async function called `init_agent` that
    takes an AgentEnvironment and configures the agent handlers.
    
    Example module::
    
        from microsoft_agents.testing import AgentEnvironment
        from microsoft_agents.activity import ActivityTypes
        
        async def init_agent(env: AgentEnvironment) -> None:
            @env.agent_application.activity(ActivityTypes.message)
            async def handle_message(context, state):
                await context.send_activity(f"Echo: {context.activity.text}")
    """
    import importlib
    
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        out.error(f"Failed to import agent module '{module_path}': {e}")
        raise click.Abort()
    
    if not hasattr(module, "init_agent"):
        out.error(f"Module '{module_path}' does not have an 'init_agent' function.")
        out.info("The module must export: async def init_agent(env: AgentEnvironment)")
        raise click.Abort()
    
    init_agent = getattr(module, "init_agent")
    
    if not callable(init_agent):
        out.error(f"'{module_path}.init_agent' is not callable.")
        raise click.Abort()
    
    return init_agent
