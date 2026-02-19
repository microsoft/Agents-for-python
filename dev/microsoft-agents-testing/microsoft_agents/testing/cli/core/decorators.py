# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""CLI command decorators.

Provides decorators for common CLI patterns such as async commands,
passing configuration/output objects, and resolving agent scenarios.
"""

import asyncio
from functools import wraps
from typing import Callable, Any

import click

from .utils import _resolve_scenario

def pass_config(func: Callable) -> Callable:
    """Decorator that injects CLIConfig from the click context.

    The decorated function receives a ``config`` keyword argument.

    :param func: The function to decorate.
    :return: The wrapped function.
    """
    @click.pass_context
    @wraps(func)
    def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        config = ctx.obj.get("config")
        if config is None:
            raise RuntimeError("CLIConfig not found in context")
        return func(config=config, *args, **kwargs)
    return wrapper

def pass_output(func: Callable) -> Callable:
    """Decorator that injects the Output helper from the click context.

    The decorated function receives an ``out`` keyword argument.

    :param func: The function to decorate.
    :return: The wrapped function.
    """
    @click.pass_context
    @wraps(func)
    def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        out = ctx.obj.get("out")
        if out is None:
            raise RuntimeError("Output not found in context")
        return func(out=out, *args, **kwargs)
    return wrapper

def async_command(func: Callable) -> Callable:
    """Decorator to run an async function as a click command.
    
    Example:
        @click.command()
        @async_command
        async def my_command():
            await some_async_operation()
    """
    
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))
    return wrapper

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
    
    @click.argument("agent_name_or_url")
    @click.option(
        "--module", "-m",
        "module_path",
        default=None,
        help="Python module path for registered agents (e.g., myproject.agents.echo).",
    )
    @click.pass_context
    @wraps(func)
    def wrapper(
        ctx: click.Context,
        agent_name_or_url: str | None,
        module_path: str | None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # Get config and output directly from context
        config = ctx.obj.get("config")
        out = ctx.obj.get("out")
        
        if config is None:
            raise RuntimeError("CLIConfig not found in context")
        if out is None:
            raise RuntimeError("Output not found in context")
        
        # Determine which scenario to use based on CLI arguments
        scenario = _resolve_scenario(
            agent_name_or_url=agent_name_or_url,
            module_path=module_path,
            config=config,
            out=out,
        )
        if not scenario:
            # Retry with 'agt.' prefix for built-in scenario shorthand names
            if agent_name_or_url:
                scenario = _resolve_scenario(
                    agent_name_or_url=f"agt.{agent_name_or_url}",
                    module_path=module_path,
                    config=config,
                    out=out,
                )
            
            if not scenario:
                out.error("Failed to locate the scenario. Please check your options.")
                raise click.Abort()
        return func(scenario=scenario, *args, **kwargs)
    
    return wrapper