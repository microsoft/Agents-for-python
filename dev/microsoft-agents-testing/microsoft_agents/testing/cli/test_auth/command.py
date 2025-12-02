import click

from .auth_sample import AuthSample

from microsoft_agents.testing.utils import resolve_env
from microsoft_agents.testing.core import AiohttpEnvironment

@click.command()
def auth_test():
    """Run authentication sample test."""

    environment = AiohttpEnvironment()
    environment.setup()

    sample = AuthSample()
    sample.run(resolve_env)