# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Main CLI entry point.

This module defines the root command group and handles initialization
such as loading environment variables and configuration.
"""

from pathlib import Path

import click

from .config import CLIConfig
from .commands import COMMANDS
from .core import Output


@click.group()
@click.option(
    "--env", "-e",
    default=".env", 
    help="Path to environment file.",
    type=click.Path(),
)
@click.option(
    "--connection", "-c",
    default="SERVICE_CONNECTION", 
    help="Named connection to use for auth credentials.",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.pass_context
def cli(ctx: click.Context, env_path: str, connection: str | None, verbose: bool) -> None:
    """Microsoft Agents Testing CLI.
    
    A command-line tool for testing and interacting with M365 Agents.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    config = CLIConfig(env_path, connection)

    out = Output(verbose=verbose)

    if env_path != ".env" and config.env_path is None:
        out.error("Specified environment file not found.")
        raise click.Abort()
    
    out.debug(f"Using environment file: {config.env_path}")
    
    ctx.obj["config"] = config


# Register all commands
for command in COMMANDS:
    cli.add_command(command)


def main() -> None:
    """Entry point for the CLI."""
    cli()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    main()
