import asyncio
import click

from microsoft_agents.testing.integration import AiohttpEnvironment

from .auth_sample import AuthScenario

async def _auth(port: int):

    scenario = AuthScenario()

    async with scenario.client() as client:
        click.echo("Auth scenario client initialized.")
        asyncio.sleep() # indefinitely?


    # Initialize the environment
    environment = AiohttpEnvironment()
    config = await AuthSample.get_config()
    await environment.init_env(config)

    sample = AuthSample(environment)
    await sample.init_app()

    host = "localhost"
    async with environment.create_runner(host, port):
        click.echo(f"\nServer running at http://{host}:{port}/api/messages\n")
        while True:
            await asyncio.sleep(10)


@click.command()
@click.option("--port", type=int, default=3978, help="Port to run the bot on.")
def auth(port: int):
    """Run the authentication testing sample from a configuration file."""
    asyncio.run(_auth(port))