import asyncio
import click

from microsoft_agents.testing.integration import AiohttpEnvironment

from .auth_sample import AuthSample

async def _test_auth(port: int):
    # Initialize the environment
    environment = AiohttpEnvironment()
    config = await AuthSample.get_config()
    await environment.init_env(config)

    sample = AuthSample(environment)
    await sample.init_app()

    host = "localhost"
    async with environment.create_runner(host, port):
        print(f"Server running at http://{host}:{port}/api/messages")
        while True:
            await asyncio.sleep(10)


@click.command()
@click.option("--port", type=int, default=3978, help="Port to run the bot on.")
async def test_auth(port: int):
    """Run the authentication testing sample from a configuration file."""
    asyncio.run(_test_auth(port))