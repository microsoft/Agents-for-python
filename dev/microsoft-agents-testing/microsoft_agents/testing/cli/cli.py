from pathlib import Path

import click
from dotenv import load_dotenv

from .cli_config import cli_config
from .commands import COMMAND_LIST

@click.group()
@click.option("--env_path", help="Environment file path")
@click.option("--connection_name", default=None, help="Connection name")
@click.pass_context
def cli(ctx, env_path, connection_name):
    """A simple CLI tool for managing tasks."""

    ctx.ensure_object(dict)
    ctx.obj["env_path"] = str(Path(env_path or ".env").absolute())

    load_dotenv(ctx.obj["env_path"], override=True)
    cli_config.load_from_config(connection_name)


for command in COMMAND_LIST:
    cli.add_command(command)
