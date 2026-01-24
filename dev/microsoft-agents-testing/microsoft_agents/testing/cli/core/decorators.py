# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Base command utilities and decorators for CLI commands."""

from functools import wraps
from typing import Callable, Any


# def require_auth(func: Callable) -> Callable:
#     """Decorator that ensures authentication config is present.
    
#     Use this on commands that require valid credentials.
    
#     Example:
#         @click.command()
#         @require_auth
#         def my_command():
#             # cli_config is guaranteed to have auth info
#             pass
#     """
#     @wraps(func)
#     def wrapper(*args: Any, **kwargs: Any) -> Any:
#         missing = cli_config.validate()
#         if missing:
#             click.secho(
#                 f"Missing required configuration: {', '.join(missing)}", 
#                 fg="red", 
#                 err=True,
#             )
#             click.echo("Please set these in your .env file or environment.")
#             raise click.Abort()
#         return func(*args, **kwargs)
#     return wrapper


# def require_agent(func: Callable) -> Callable:
#     """Decorator that ensures agent URL is configured.
    
#     Use this on commands that need to connect to an agent.
#     """
#     @wraps(func)
#     def wrapper(*args: Any, **kwargs: Any) -> Any:
#         if not cli_config.agent_url:
#             click.secho(
#                 "No agent URL configured. Set AGENT_URL in your .env file.", 
#                 fg="red", 
#                 err=True,
#             )
#             raise click.Abort()
#         return func(*args, **kwargs)
#     return wrapper


def async_command(func: Callable) -> Callable:
    """Decorator to run an async function as a click command.
    
    Example:
        @click.command()
        @async_command
        async def my_command():
            await some_async_operation()
    """
    import asyncio
    
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))
    return wrapper
