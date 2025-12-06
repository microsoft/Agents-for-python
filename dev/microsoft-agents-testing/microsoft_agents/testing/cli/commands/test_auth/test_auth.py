# import click

# from .auth_sample import AuthSample

# from microsoft_agents.testing.utils import resolve_env
# from microsoft_agents.testing.core import AiohttpEnvironment


# @click.command()
# def auth_test():
#     """Run authentication sample test."""

#     environment = AiohttpEnvironment()
#     environment.setup()

#     sample = AuthSample()
#     sample.run(resolve_env)

import click

# from .auth_sample import auth_sample

@click.command()
def test_auth():
    """Run the authentication testing sample from a configuration file."""

    # # Load the configuration file
    # config = load_config_file()

    # # Initialize the environment
    # environment = AiohttpEnvironment(config)

    # # Set up the environment
    # environment.setup()

    # # Run the authentication sample test
    # sample = auth_sample()
    # sample.run(resolve_env)