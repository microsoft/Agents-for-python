import pytest

from microsoft_agents.testing import AgentClient

@pytest.mark.agent_test("my_agent")
async def test_my_agent(agent_client: AgentClient):

    await agent_client.send("Hello, World!", wait=5.0)

    # assert that the agent replied with a message Activity
    agent_client.expect().that_for_any(type="message")