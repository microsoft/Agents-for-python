from pathlib import Path

import click
from dotenv import load_dotenv

from microsoft_agents.testing.utils import resolve_env

from .cli_config import cli_config
from .commands import COMMAND_LIST

@click.group()
@click.option("--env_path", default=".env", help="Environment file path")
@click.option("--connection_name", default=None, help="Connection name")
@click.pass_context
def cli(ctx, env_path, connection_name):
    """A simple CLI tool for managing tasks."""

    click.echo("-"*80)
    click.echo("Welcome to the CLI for the microsoft-agents-testing package for Python.")

    ctx.ensure_object(dict)

    env_path = Path(env_path)

    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found at: {env_path.absolute()}")
    

    env_path = str(env_path.resolve())
    load_dotenv(env_path, override=True)
    click.echo("\tUsing environment file at: " + env_path)
    click.echo()

    ctx.obj["env_path"] = env_path
    
    cli_config.load_from_config(connection_name)



for command in COMMAND_LIST:
    cli.add_command(command)
