import os
import asyncio

from dotenv import load_dotenv

from microsoft_agents.testing import (
    AiohttpEnvironment,
    AgentClient,
)
from .quickstart_sample import QuickstartSample


async def main():

    env = AiohttpEnvironment()
    await env.init_env(await QuickstartSample.get_config())
    sample = QuickstartSample(env)
    await sample.init_app()

    host, port = "localhost", 3978

    load_dotenv("./src/tests/.env")
    config = {
        "client_id": os.getenv(
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID", ""
        ),
        "tenant_id": os.getenv(
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID", ""
        ),
        "client_secret": os.getenv(
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET", ""
        ),
    }

    client = AgentClient(
        agent_url="http://localhost:3978/",
        cid=config.get("cid", ""),
        client_id=config.get("client_id", ""),
        tenant_id=config.get("tenant_id", ""),
        client_secret=config.get("client_secret", ""),
    )

    async with env.create_runner(host, port):
        print(f"Server running at http://{host}:{port}/api/messages")
        await asyncio.sleep(1)
        res = await client.send_expect_replies("Hello, Agent!")
        print("\nReply from agent:")
        print(res)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
