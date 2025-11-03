import pytest
import asyncio

from src.core import integration, IntegrationFixtures, AiohttpEnvironment, AiohttpEnvironment
from src.samples import QuickstartSample

async def main():

    env = AiohttpEnvironment()
    await env.init_env(await QuickstartSample.get_config())
    sample = QuickstartSample(env)
    await sample.init_app()

    host, port = "localhost", 3978

    async with env.create_runner(host, port):
        print(f"Server running at http://{host}:{port}/api/messages")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())