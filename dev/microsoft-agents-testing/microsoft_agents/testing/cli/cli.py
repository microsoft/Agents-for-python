import click
from dotenv import load_dotenv

from .cli_config import cli_config
from .commands import COMMAND_LIST

@click.group()
@click.option("--env_path", help="Environment file path")
@click.option("--connection_name", default=None, help="Connection name")
def cli(env_path, connection_name):
    """A simple CLI tool for managing tasks."""

    load_dotenv()

    if env_path:
        load_dotenv(env_path)
        cli_config.load_from_config(connection_name)


for command in COMMAND_LIST:
    cli.add_command(command)
