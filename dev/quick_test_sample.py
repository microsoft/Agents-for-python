import os
import asyncio

from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState
)
from microsoft_agents.testing import (
    AiohttpEnvironment,
    AgentClient,
    Sample
)

async def run_interactive(sample_cls: type[Sample]) -> None:

    env = AiohttpEnvironment()
    await env.init_env(await sample_cls.get_config())
    sample = sample_cls(env)
    await sample.init_app()

    host, port = "localhost", 3978

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
        user_input = input(">> ")
        res = await client.send_expect_replies(user_input)
        print()
        print()
        print(res)
        print()

    await client.close()

class MySample(Sample):

    @classmethod
    async def get_config(cls) -> dict:
        """Retrieve the configuration for the sample."""
        load_dotenv()
        return dict(os.environ)

    async def init_app(self):
        """Initialize the application for the quickstart sample."""

        app: AgentApplication[TurnState] = self.env.agent_application

        @app.activity("message")
        async def on_message(context: TurnContext, state: TurnState) -> None:
            await context.send_activity(f"you said: {context.activity.text}")

if __name__ == "__main__":
    asyncio.run(run_interactive(MySample))