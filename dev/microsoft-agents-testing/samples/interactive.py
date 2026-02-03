import asyncio

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState
)
from microsoft_agents.testing import (
    AiohttpScenario,
    AgentEnvironment,
)

async def init_app(env: AgentEnvironment) -> None:
    """Initialize the application for the quickstart sample."""

    app: AgentApplication[TurnState] = env.agent_application

    @app.activity("message")
    async def on_message(context: TurnContext, state: TurnState) -> None:
        await context.send_activity(f"you said: {context.activity.text}")

scenario = AiohttpScenario(init_app)

async def main():

    async with scenario.client() as agent_client:
        print(f"Agent running...")
        await asyncio.sleep(.1)
        user_input = input(">> ")
        res = await agent_client.send_expect_replies(user_input)
        print()
        for act in res:
            print(f"Agent: {act.text}")
        print(res)
        print()

if __name__ == "__main__":
    asyncio.run(main())