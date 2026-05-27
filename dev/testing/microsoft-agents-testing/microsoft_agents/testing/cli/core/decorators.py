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

    Adds ``--url``/``-u`` and ``--agent``/``-a`` options to the command.
    Exactly one must be provided. The decorated function receives the resolved
    ``Scenario`` instance via a ``scenario`` keyword argument.

    Example::

        @click.command()
        @with_scenario
        @async_command
        async def chat(scenario: Scenario) -> None:
            async with scenario.client() as client:
                replies = await client.send_expect_replies("Hello!")
                for reply in replies:
                    print(f"Agent: {reply.text}")

    The decorator supports two modes:

    1. External Agent Mode (``--url``):
       Creates an ``ExternalScenario`` that sends HTTP requests to an agent
       already running at the given URL.

       Example: ``agt scenario chat --url http://localhost:3978/api/messages``

    2. Registered Scenario Mode (``--agent``):
       Looks up a named scenario in the scenario registry.  Use ``--module``
       to import a module first if its scenarios are not yet registered.

       Example: ``agt scenario chat --agent agt.basic``
    """
    
    @click.option(
        "--url", "-u",
        "agent_url",
        default=None,
        help="URL of the external agent to connect to.",
    )
    @click.option(
        "--agent", "-a",
        "agent_name",
        default=None,
        help="Name of the agent to use.",
    )
    @click.option(
        "--module",
        "module_path",
        default=None,
        help="Python module path for registered agents (e.g., myproject.agents.echo).",
    )
    @click.pass_context
    @wraps(func)
    def wrapper(
        ctx: click.Context,
        agent_url: str | None,
        agent_name: str | None,
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
        
        if agent_url and agent_name:
            out.error("Only one of --url or --agent can be specified.", exit=True)
        elif not agent_url and not agent_name:
            out.error("Either --url or --agent must be specified.", exit=True)

        agent_name_or_url = agent_url or agent_name
        
        # Determine which scenario to use based on CLI arguments
        scenario = _resolve_scenario(
            agent_name_or_url=agent_name_or_url,
            module_path=module_path,
            config=config,
            out=out,
        )
        if not scenario:
            # Retry with 'agt.' prefix for built-in scenario shorthand names
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