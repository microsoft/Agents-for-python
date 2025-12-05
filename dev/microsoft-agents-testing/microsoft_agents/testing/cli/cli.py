import click

from .commands import COMMAND_LIST

@click.group()
def cli():
    pass

for command in COMMAND_LIST:
    cli.add_command(command)